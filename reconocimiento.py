"""
reconocimiento.py
Usa el modelo entrenado (modelo_rostros.yml) para reconocer caras en vivo con la webcam
y envía comandos por serial a un Arduino.

Protocolo con Arduino:
- Si se reconoce a alguien autorizado: se envía el carácter 'G'
- Si la cara es desconocida: se envía el carácter 'R'
"""

import cv2
import os
from pathlib import Path
import pickle
import serial
import time

# ------------- CONFIGURACIÓN BÁSICA -------------

# Carpeta donde está este archivo reconocimiento.py
BASE_DIR = Path(__file__).resolve().parent

# Rutas de archivos del modelo y las etiquetas
MODEL_PATH = BASE_DIR / "modelo_rostros.yml"
LABELS_PATH = BASE_DIR / "labels.pkl"

# Puerto serie del Arduino (ajústalo si usas otro COM)
SERIAL_PORT = "COM3"
BAUD_RATE = 115200

# Umbral de confianza para decidir si la cara es conocida
# (cuanto más bajo, más estricta la comparación)
CONFIDENCE_THRESHOLD = 70.0

# ------------- CARGA DE CLASIFICADOR HAAR -------------

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
print("Usando cascade en:", CASCADE_PATH, "; ¿Existe?", os.path.exists(CASCADE_PATH))

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if face_cascade.empty():
    raise FileNotFoundError(f"No se pudo cargar el clasificador Haar: {CASCADE_PATH}")

# ------------- CARGA DE MODELO Y LABELS -------------

print("Cargando modelo y etiquetas...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo del modelo: {MODEL_PATH}\n"
        f"Asegúrate de haber ejecutado primero entrenar.py."
    )

if not LABELS_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo de etiquetas: {LABELS_PATH}\n"
        f"Asegúrate de haber ejecutado primero entrenar.py."
    )

# Cargamos el modelo LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(str(MODEL_PATH))

# Cargamos el diccionario {nombre: id} y lo invertimos a {id: nombre}
with open(LABELS_PATH, "rb") as f:
    label_ids = pickle.load(f)

id_to_name = {v: k for k, v in label_ids.items()}
print("Etiquetas cargadas:", id_to_name)

# ------------- CONFIGURACIÓN DEL PUERTO SERIE -------------

ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # tiempo para que Arduino reinicie
    print(f"[SERIAL] Conectado a {SERIAL_PORT}")
except Exception as e:
    print(f"[SERIAL] No se pudo abrir el puerto {SERIAL_PORT}: {e}")
    print("El programa seguirá funcionando pero no enviará comandos al Arduino.")
    ser = None

def enviar_serial(codigo: str):
    """Envía un carácter por serial si el puerto está disponible."""
    if ser is not None and ser.is_open:
        try:
            ser.write(codigo.encode("utf-8"))
        except Exception as e:
            print(f"[SERIAL] Error enviando '{codigo}': {e}")

# ------------- CAPTURA DE VIDEO Y RECONOCIMIENTO -------------

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara (índice 0).")

print("Iniciando reconocimiento. Pulsa 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer un frame de la cámara.")
        break

    # Convertimos a escala de grises (LBPH trabaja en gris)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detectamos caras
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(50, 50)
    )

    # Para cada cara detectada, intentamos reconocerla
    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]

        # LBPH espera una imagen en escala de grises
        label_id, confidence = recognizer.predict(face_roi)

        # Por defecto asumimos que la cara es desconocida
        nombre = "Desconocido"
        color_rect = (0, 0, 255)  # rectángulo rojo para desconocido

        if confidence < CONFIDENCE_THRESHOLD and label_id in id_to_name:
            # Cara conocida y dentro del umbral de confianza
            nombre = id_to_name[label_id]
            color_rect = (0, 255, 0)  # rectángulo verde para conocida
            enviar_serial("G")        # cara reconocida -> LED verde en Arduino
        else:
            # Cara desconocida o confianza demasiado baja
            enviar_serial("R")        # cara desconocida -> LED rojo en Arduino

        # Dibujamos rectángulo alrededor de la cara
        cv2.rectangle(frame, (x, y), (x+w, y+h), color_rect, 2)

        # Mostramos nombre y confianza encima del rectángulo
        texto = f"{nombre} ({confidence:.1f})"
        cv2.putText(frame, texto, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_rect, 2)

    # Mostramos la imagen con las detecciones
    cv2.imshow("Reconocimiento facial", frame)

    # Salir con la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ------------- LIMPIEZA FINAL -------------

cap.release()
cv2.destroyAllWindows()

if ser is not None and ser.is_open:
    ser.close()
    print("[SERIAL] Puerto cerrado.")
