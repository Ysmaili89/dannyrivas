import sys
import os

# ====== CONFIGURACIÓN (CAMBIA ESTOS VALORES) ======
# Tu nombre de usuario en PythonAnywhere
USERNAME = 'Ysmailin89'

# Ruta a tu aplicación (cambia si usas otra carpeta)
PROJECT_PATH = f'/home/{USERNAME}/dannyrivas'

# Nombre de tu entorno virtual
VENV_NAME = 'ministerio'
# =================================================

# Agregar el proyecto al path
if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

# Activar el entorno virtual de forma manual
VENV_PATH = f'/home/{USERNAME}/.virtualenvs/{VENV_NAME}'
activate_this = os.path.join(VENV_PATH, 'bin', 'activate_this.py')

if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})
    print(f"✅ Virtualenv {VENV_NAME} activado")
else:
    print(f"❌ No se encontró el virtualenv en {activate_this}")

# Importar la aplicación
try:
    from app import application
    print("✅ App importada correctamente")
except Exception as e:
    print(f"❌ Error importando app: {e}")
    raise