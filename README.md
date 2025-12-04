# Guía de Uso del Software

## 1. Iniciar el Sistema
Para ingresar, abre **PowerShell** y ejecuta los siguientes comandos en orden:

```powershell
# 1. Navegar a la carpeta del proyecto
cd "INGRESA_LA_RUTA_DE_LA_CARPETA_USADA_PARA_LOS_SCRIPTS"

# 2. Permisos de ejecución (solo para esta sesión)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Activar entorno virtual
.\venv\Scripts\Activate.ps1

# 4. Iniciar reconocimiento
python reconocimiento.py