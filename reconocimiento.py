"""
reconocimiento.py - Sistema de Reconocimiento Facial con Zabbix
Versión mejorada para monitoreo con Zabbix
"""

import cv2
import os
from pathlib import Path
import pickle
import serial
import time
import numpy as np
from datetime import datetime

# ========== CONFIGURACIÓN ZABBIX ==========
try:
    from pyzabbix import ZabbixMetric, ZabbixSender
    ZABBIX_DISPONIBLE = True
    print("[✓] pyzabbix importado correctamente")
except ImportError as e:
    ZABBIX_DISPONIBLE = False
    print(f"[✗] pyzabbix no instalado: {e}")

ZABBIX_SERVER_IP = "192.168.99.7"
ZABBIX_HOST = "UbuntuFacial"

def enviar_metrica_zabbix(clave, valor):
    """Envía una métrica a Zabbix."""
    if not ZABBIX_DISPONIBLE:
        print(f"[ZABBIX DESHABILITADO] No se envía {clave} = {valor}")
        return
    try:
        packet = [ZabbixMetric(ZABBIX_HOST, clave, valor)]
        sender = ZabbixSender(zabbix_server=ZABBIX_SERVER_IP, timeout=2)
        response = sender.send(packet)
        print(f"[ZABBIX ✓] {clave} = {valor} | Host: {ZABBIX_HOST}")
        return response
    except Exception as e:
        print(f"[ZABBIX ERROR] {clave} | {e}")

# ========== CONFIGURACIÓN BÁSICA ==========
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "modelo_rostros.yml"
LABELS_PATH = BASE_DIR / "labels.npy"

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
CONFIDENCE_THRESHOLD = 70.0
SHOW_WINDOW = True
CHECK_INTERVAL = 30

# Variables de estado
base_rostros_dir = BASE_DIR / "base_rostros"
last_base_rostros_state = None
rostros_totales = 0
rostros_reconocidos = 0
rostros_desconocidos = 0

# Sistema de cooldown para evitar detecciones repetidas
ultimo_reconocimiento = {}
COOLDOWN_SEGUNDOS = 5
rostros_en_frame_anterior = set()

# ========== CARGA DE CLASIFICADOR ==========
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
print(f"Usando cascade: {CASCADE_PATH}")

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if face_cascade.empty():
    raise FileNotFoundError(f"No se pudo cargar: {CASCADE_PATH}")

# ========== CARGA DE MODELO Y ETIQUETAS ==========
print("Cargando modelo y etiquetas...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Modelo no encontrado: {MODEL_PATH}")

if not LABELS_PATH.exists():
    raise FileNotFoundError(f"Etiquetas no encontradas: {LABELS_PATH}")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(str(MODEL_PATH))

# Cargar etiquetas
try:
    label_data = np.load(str(LABELS_PATH), allow_pickle=True).item()
    label_ids = label_data if isinstance(label_data, dict) else label_data
except Exception as e:
    try:
        with open(LABELS_PATH, "rb") as f:
            label_ids = pickle.load(f)
    except Exception as e2:
        print(f"[ERROR] No se pudieron cargar etiquetas: {e2}")
        label_ids = {}

id_to_name = {v: k for k, v in label_ids.items()}
print(f"Personas disponibles: {list(id_to_name.values())}")
enviar_metrica_zabbix('personas_en_sistema', len(id_to_name))

# ========== PUERTO SERIE ==========
ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"[SERIAL] Conectado a {SERIAL_PORT}")
except Exception as e:
    print(f"[SERIAL] Error: {e}")
    ser = None

def enviar_serial(codigo: str):
    """Envía comando al Arduino."""
    if ser is not None and ser.is_open:
        try:
            ser.write(codigo.encode("utf-8"))
        except Exception as e:
            print(f"[SERIAL ERROR] {e}")

# ========== FUNCIONES DE MONITOREO ==========
def obtener_carpetas_personas():
    """Obtiene carpetas en base_rostros."""
    try:
        if base_rostros_dir.exists():
            return set([d.name for d in base_rostros_dir.iterdir() if d.is_dir()])
        return set()
    except Exception as e:
        print(f"[ERROR] {e}")
        return set()

def entrenar_modelo_automatico():
    """Reentrena modelo cuando cambia base_rostros."""
    global recognizer, id_to_name, label_ids
    
    print("\n[REENTRENAMIENTO] Entrenando automáticamente...")
    
    try:
        face_images = []
        face_ids = []
        label_ids = {}
        current_id = 0
        
        for person_dir in base_rostros_dir.iterdir():
            if not person_dir.is_dir():
                continue
            
            person_name = person_dir.name
            if person_name not in label_ids:
                label_ids[person_name] = current_id
                current_id += 1
            
            person_id = label_ids[person_name]
            
            for img_path in person_dir.iterdir():
                if not img_path.is_file():
                    continue
                try:
                    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        continue
                    
                    faces = face_cascade.detectMultiScale(img, 1.2, 5, minSize=(50, 50))
                    
                    if len(faces) == 0:
                        face_images.append(img)
                        face_ids.append(person_id)
                    else:
                        for (x, y, w, h) in faces:
                            face_roi = img[y:y+h, x:x+w]
                            face_images.append(face_roi)
                            face_ids.append(person_id)
                except Exception as e:
                    continue
        
        if len(face_images) > 0:
            faces_array = [cv2.resize(f, (100, 100)) for f in face_images]
            faces_array = np.array(faces_array)
            ids_array = np.array(face_ids)
            
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(faces_array, ids_array)
            recognizer.write(str(MODEL_PATH))
            
            np.save(LABELS_PATH, label_ids)
            id_to_name = {v: k for k, v in label_ids.items()}
            
            print(f"✓ Modelo reentrenado")
            print(f"✓ Personas: {list(id_to_name.values())}")
            enviar_metrica_zabbix('personas_en_sistema', len(id_to_name))
            return True
        else:
            print("[ADVERTENCIA] Sin imágenes para entrenar")
            label_ids = {}
            id_to_name = {}
            np.save(LABELS_PATH, label_ids)
            enviar_metrica_zabbix('personas_en_sistema', 0)
            return False
    except Exception as e:
        print(f"[ERROR] Reentrenamiento: {e}")
        return False

def verificar_cambios_base_rostros():
    """Verifica cambios en base_rostros y reentrena si es necesario."""
    global last_base_rostros_state
    
    current_state = obtener_carpetas_personas()
    
    if last_base_rostros_state is not None and current_state != last_base_rostros_state:
        print("[CAMBIO DETECTADO] Carpetas modificadas")
        eliminadas = last_base_rostros_state - current_state
        nuevas = current_state - last_base_rostros_state
        
        if eliminadas:
            print(f"✗ Eliminadas: {eliminadas}")
        if nuevas:
            print(f"✓ Nuevas: {nuevas}")
        
        entrenar_modelo_automatico()
        return True
    
    return False

# ========== CÁMARA ==========
print("Abriendo cámara...")
cap = None
for idx in range(3):
    try:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            print(f"✓ Cámara abierta (índice {idx})")
            break
    except:
        continue

if cap is None or not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara")

print("Iniciando reconocimiento...")
frame_count = 0
last_base_rostros_state = obtener_carpetas_personas()
enviar_metrica_zabbix('estado_aplicacion', 'ENCENDIDO')

# ========== INICIO DEL WHILE TRUE PRINCIPAL ==========
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer frame")
            break

        # Verificar cambios cada 30 frames
        frame_count += 1
        if frame_count % CHECK_INTERVAL == 0:
            verificar_cambios_base_rostros()
            frame_count = 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(50, 50))

        rostros_en_frame_actual = set()

        # ========== DETECCIÓN Y RECONOCIMIENTO ==========
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            label_id, confidence = recognizer.predict(face_roi)

            nombre = "Desconocido"
            color_rect = (0, 0, 255)

            tiempo_actual = time.time()

            if confidence < CONFIDENCE_THRESHOLD and label_id in id_to_name:
                # ========== CARA RECONOCIDA ==========
                nombre = id_to_name[label_id]
                color_rect = (0, 255, 0)

                rostros_en_frame_actual.add(nombre)

                if nombre not in ultimo_reconocimiento or (tiempo_actual - ultimo_reconocimiento[nombre]) > COOLDOWN_SEGUNDOS:
                    enviar_serial("G")
                    rostros_reconocidos += 1
                    enviar_metrica_zabbix('acceso.exitoso', 1)
                    enviar_metrica_zabbix('persona_reconocida', nombre)
                    ultimo_reconocimiento[nombre] = tiempo_actual
                    print(f"[ACCESO] {nombre} - Confianza: {confidence:.1f}")
            else:
                # ========== CARA DESCONOCIDA ==========
                rostros_en_frame_actual.add("Desconocido")

                if "Desconocido" not in ultimo_reconocimiento or (tiempo_actual - ultimo_reconocimiento["Desconocido"]) > COOLDOWN_SEGUNDOS:
                    enviar_serial("R")
                    rostros_desconocidos += 1
                    enviar_metrica_zabbix('acceso.fallido', 1)
                    enviar_metrica_zabbix('persona_reconocida', nombre)
                    ultimo_reconocimiento["Desconocido"] = tiempo_actual
                    print(f"[DENEGADO] Desconocido - Confianza: {confidence:.1f}")

            # Dibujar
            cv2.rectangle(frame, (x, y), (x+w, y+h), color_rect, 2)
            texto = f"{nombre} ({confidence:.1f})"
            cv2.putText(frame, texto, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_rect, 2)

        rostros_en_frame_anterior = rostros_en_frame_actual

        # Mostrar ventana
        if SHOW_WINDOW:
            cv2.imshow("Reconocimiento facial", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# ========== FIN DEL WHILE TRUE PRINCIPAL ==========
except KeyboardInterrupt:
    print("\n[DETENIDO] Ctrl+C")

# ========== LIMPIEZA FINAL ==========
cap.release()
cv2.destroyAllWindows()

if ser is not None and ser.is_open:
    ser.close()
    print("[SERIAL] Puerto cerrado")

enviar_metrica_zabbix('estado_aplicacion', 'APAGADO')
print("[INFO] Aplicación terminada")
print(f"Estadísticas:")
print(f"  Rostros totales: {rostros_totales}")
print(f"  Reconocidos: {rostros_reconocidos}")
print(f"  Desconocidos: {rostros_desconocidos}")
