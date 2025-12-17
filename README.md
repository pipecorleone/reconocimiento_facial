Este documento explica cómo instalar y ejecutar el proyecto **en Linux y Windows**, priorizando un flujo de trabajo **orientado a Linux** (que es el escenario típico para este tipo de despliegues), pero dejando pasos equivalentes para Windows.

Repositorio: `pipecorleone/reconocimiento_facial` (rama `master`). citeturn9view2

---

## 1) ¿Qué incluye el repositorio?

En la raíz del proyecto se encuentran, entre otros, los siguientes archivos (nombres exactos): `entrenar.py`, `reconocimiento.py`, `requirements.txt`, `modelo_rostros.yml` y `labels.npy`. citeturn9view2

- **`entrenar.py`**: script de entrenamiento (genera/actualiza el modelo).
- **`reconocimiento.py`**: script de reconocimiento (usa el modelo entrenado).
- **`requirements.txt`**: dependencias de Python. citeturn9view2
- **`modelo_rostros.yml`** y **`labels.npy`**: artefactos del modelo/diccionario de etiquetas (pueden regenerarse al re-entrenar). citeturn9view2
- Carpeta **`sketch_nov22a/`**: sketch asociado a Arduino (uso opcional). citeturn9view2

---

## 2) Requisitos previos

### Hardware
- Cámara web (integrada o USB).
- (Opcional) Arduino y cable USB, si se utiliza el sketch incluido.

### Software mínimo
- **Git**
- **Python 3** (idealmente 3.9+)
- **pip** (gestor de paquetes de Python)
- Soporte para **venv** (entornos virtuales)

---

## 3) Instalación (Linux)

> Ejemplos pensados para Ubuntu/Debian. En otras distribuciones, los paquetes equivalentes cambian de nombre.

### 3.1. Paquetes del sistema (recomendado)
Estos paquetes suelen evitar errores típicos de OpenCV relacionados con librerías gráficas o de video:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git   libgl1 libglib2.0-0
```

Si se usan cámaras V4L2 y hay problemas de permisos, ver la sección **Troubleshooting**.

### 3.2. Clonar el repositorio
```bash
git clone https://github.com/pipecorleone/reconocimiento_facial.git
cd reconocimiento_facial
```

### 3.3. Crear y activar entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

> Tip: para desactivar luego, usar `deactivate`.

### 3.4. Instalar dependencias
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4) Instalación (Windows)

> El README actual del repo muestra un flujo por PowerShell para activar el `venv` y ejecutar `reconocimiento.py`. citeturn9view2  
> A continuación se deja un flujo “limpio” y completo (incluye creación del `venv` e instalación de requisitos).

### 4.1. Clonar el repositorio
En PowerShell o CMD:

```powershell
git clone https://github.com/pipecorleone/reconocimiento_facial.git
cd reconocimiento_facial
```

### 4.2. Crear y activar entorno virtual
```powershell
python -m venv venv
```

Activar (PowerShell):
```powershell
# Permisos de ejecución solo para la sesión actual (si es necesario)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.env\Scripts\Activate.ps1
```

> Este paso está alineado con lo que aparece en el README del repositorio. citeturn9view2

### 4.3. Instalar dependencias
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5) Flujo de uso recomendado

### 5.1. Entrenar / actualizar el modelo
Desde la carpeta del proyecto, con el entorno virtual **activo**:

Linux:
```bash
python3 entrenar.py
```

Windows:
```powershell
python entrenar.py
```

Resultado esperado:
- Al terminar, el proyecto debería tener (o actualizar) los artefactos del modelo (por ejemplo `modelo_rostros.yml` y `labels.npy`). 

> Nota: los detalles exactos del dataset (carpetas, cantidad de imágenes, etc.) dependen de cómo `entrenar.py` esté implementado. Si el entrenamiento solicita capturas por cámara o una ruta de imágenes, se recomienda seguir el prompt/flujo que muestre por consola.

### 5.2. Ejecutar el reconocimiento en tiempo real
Con el entorno virtual **activo**:

Linux:
```bash
python3 reconocimiento.py
```

Windows:
```powershell
python reconocimiento.py
```



---

## 6) Uso con Arduino (opcional)

El repositorio incluye una carpeta `sketch_nov22a/`. citeturn9view2  
Sin embargo, la integración exacta (puerto serie, baudrate, protocolo de mensajes) depende de la implementación de tu script Python y del sketch.

Recomendación práctica de integración:
1. Cargar el sketch en Arduino (Arduino IDE).
2. Conectar Arduino por USB y verificar el puerto:
   - Linux: `ls /dev/ttyUSB* /dev/ttyACM*`
   - Windows: Administrador de dispositivos → “Puertos (COM y LPT)”
3. En caso de que `reconocimiento.py` use Serial, asegurar:
   - Puerto correcto
   - Baudrate correcto
   - Permisos (Linux)

---

## 7) Troubleshooting (problemas típicos)

### 7.1. Linux: “Permission denied” al acceder a la cámara
- Verificar que la cámara exista:
  ```bash
  ls -l /dev/video*
  ```
- Agregar el usuario al grupo `video` y reiniciar sesión:
  ```bash
  sudo usermod -aG video $USER
  ```
  Luego cerrar sesión y entrar nuevamente.

### 7.2. Linux: errores `libGL` / `libglib` / ventanas no abren
Instalar dependencias del sistema (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install -y libgl1 libglib2.0-0
```

### 7.3. Windows: no se puede activar `Activate.ps1`
Ejecutar (PowerShell) antes de activar:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Luego:
```powershell
.env\Scripts\Activate.ps1
```
Esto coincide con el enfoque descrito en el README. citeturn9view2

### 7.4. “ModuleNotFoundError: cv2” o dependencias faltantes
- Confirmar que el entorno virtual esté activo.
- Reinstalar dependencias:
  ```bash
  pip install -r requirements.txt
  ```

---

## 8) Recomendaciones para documentar el proyecto (si es para informe)

- Declarar explícitamente el flujo:
  1) instalación → 2) entrenamiento → 3) reconocimiento.
- Aclarar que el modelo se materializa en artefactos (`modelo_rostros.yml`, `labels.npy`) y que se consumen en ejecución. citeturn9view2
- Para una implantación en Linux (servidor o mini-PC), dejar indicado:
  - versión de Python
  - cómo se activó `venv`
  - dependencias del sistema instaladas
  - permisos de cámara/serial (si aplica)

---

## 9) Comandos “rápidos” (resumen)

### Linux (rápido)
```bash
git clone https://github.com/pipecorleone/reconocimiento_facial.git
cd reconocimiento_facial
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 entrenar.py
python3 reconocimiento.py
```

### Windows (rápido)
```powershell
git clone https://github.com/pipecorleone/reconocimiento_facial.git
cd reconocimiento_facial
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.env\Scripts\Activate.ps1
pip install -r requirements.txt
python entrenar.py
python reconocimiento.py
```

---
