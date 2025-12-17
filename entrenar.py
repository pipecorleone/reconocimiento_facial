"""
entrenar.py
Entrena un modelo de reconocimiento facial LBPH a partir de la carpeta base_rostros.

Estructura esperada:
RECONOCIMIENTO_FACIAL/
    base_rostros/
        Diego/
            img1.jpg
            img2.jpg
        Invitado1/
            foto1.png
        ...

Cada subcarpeta dentro de base_rostros se toma como el nombre de la persona.
"""

import cv2
import numpy as np
import os
from pathlib import Path

# --- Rutas base ---

# Carpeta donde está este archivo entrenar.py
BASE_DIR = Path(__file__).resolve().parent

# Carpeta que hace de "mini base de datos" de rostros
DATA_DIR = BASE_DIR / "base_rostros"

# Archivo donde se guardará el modelo entrenado LBPH
MODEL_PATH = BASE_DIR / "modelo_rostros.yml"

# Archivo donde se guardará el diccionario {nombre_persona: id}
LABELS_PATH = BASE_DIR / "labels.npy"

# --- Cargamos el clasificador Haar incluido en OpenCV ---

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
print("Usando cascade en:", CASCADE_PATH, "; ¿Existe?", os.path.exists(CASCADE_PATH))

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
if face_cascade.empty():
    raise FileNotFoundError(f"No se pudo cargar el clasificador Haar: {CASCADE_PATH}")

# --- Recorremos base_rostros y construimos dataset ---

# Lista con las imágenes de caras (todas convertidas a escala de grises)
face_images = []

# Lista con los ids numéricos asociados a cada cara
face_ids = []

# Diccionario nombre -> id
label_ids = {}
current_id = 0

print(f"Buscando imágenes en: {DATA_DIR}")

if not DATA_DIR.exists():
    raise FileNotFoundError(
        f"No se encontró la carpeta base_rostros en: {DATA_DIR}\n"
        f"Crea esta carpeta y dentro subcarpetas con el nombre de la persona."
    )

# Recorremos todas las subcarpetas de base_rostros
for person_dir in DATA_DIR.iterdir():
    if not person_dir.is_dir():
        continue  # Ignorar archivos sueltos

    person_name = person_dir.name  # nombre de la persona (nombre de la carpeta)

    # Asignamos un id numérico a cada persona
    if person_name not in label_ids:
        label_ids[person_name] = current_id
        current_id += 1

    person_id = label_ids[person_name]

    print(f"Procesando persona: {person_name} (id={person_id})")

    # Recorremos las imágenes dentro de la carpeta de esa persona
    for img_path in person_dir.iterdir():
        if not img_path.is_file():
            continue

        # Cargamos imagen en escala de grises
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[ADVERTENCIA] No se pudo leer la imagen: {img_path}")
            continue

        # Detectamos caras en la imagen
        faces = face_cascade.detectMultiScale(
            img,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(50, 50)
        )

        if len(faces) == 0:
            # Si no se detecta cara, se puede descartar o usar la imagen completa.
            print(f"[ADVERTENCIA] No se detectó cara en {img_path.name}, usando imagen completa.")
            face_images.append(img)
            face_ids.append(person_id)
        else:
            # Para cada cara detectada, recortamos la región y la añadimos al dataset
            for (x, y, w, h) in faces:
                face_roi = img[y:y+h, x:x+w]
                face_images.append(face_roi)
                face_ids.append(person_id)

print("Total de imágenes de caras:", len(face_images))
print("Total de personas (ids únicos):", len(label_ids))

if len(face_images) == 0:
    raise RuntimeError(
        "No se encontraron caras para entrenar. "
        "Revisa que las imágenes tengan rostros visibles."
    )

# Convertimos listas a arrays de NumPy
faces_array = [cv2.resize(f, (100, 100)) for f in face_images]  # normalizamos tamaño
faces_array = np.array(faces_array)
ids_array = np.array(face_ids)

# --- Entrenamos el modelo LBPH ---

print("Entrenando modelo LBPH...")
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces_array, ids_array)

# Guardamos el modelo en un archivo .yml
recognizer.write(str(MODEL_PATH))
print("Modelo guardado en:", MODEL_PATH)

# --- Guardamos el diccionario de labels ({nombre: id}) con numpy ---

np.save(LABELS_PATH, label_ids)

print("Etiquetas guardadas en:", LABELS_PATH)
print("Diccionario nombre -> id:", label_ids)
print("Entrenamiento completado.")
