"""
WSGI configuration for PythonAnywhere
Ministerio Jhonatan Danny Rivas
"""

import sys
import os
import traceback

# ====== CONFIGURACIÓN (CAMBIA ESTOS VALORES SI ES NECESARIO) ======
# Tu nombre de usuario en PythonAnywhere
USERNAME = 'Ysmailin89'

# Ruta a tu aplicación (cambia si usas otra carpeta)
PROJECT_PATH = f'/home/{USERNAME}/dannyrivas'

# Nombre de tu entorno virtual
VENV_NAME = 'ministerio'
# =================================================================

# Agregar el proyecto al path
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)
    print(f"✅ Proyecto agregado al path: {PROJECT_PATH}")

# Agregar también el directorio padre (por si acaso)
parent_path = os.path.dirname(PROJECT_PATH)
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

# Configurar variable de entorno para PythonAnywhere
os.environ['PYTHONANYWHERE_DOMAIN'] = 'pythonanywhere.com'

# Activar el entorno virtual de forma manual
VENV_PATH = f'/home/{USERNAME}/.virtualenvs/{VENV_NAME}'
activate_this = os.path.join(VENV_PATH, 'bin', 'activate_this.py')

if os.path.exists(activate_this):
    try:
        with open(activate_this) as f:
            exec(f.read(), {'__file__': activate_this})
        print(f"✅ Virtualenv {VENV_NAME} activado correctamente")
    except Exception as e:
        print(f"⚠️ Error activando virtualenv: {e}")
        print("   Continuando sin virtualenv...")
else:
    print(f"⚠️ No se encontró el virtualenv en {activate_this}")
    print("   Usando Python del sistema...")
    
    # Verificar si las dependencias están instaladas globalmente
    try:
        import flask
        print(f"✅ Flask {flask.__version__} encontrado globalmente")
    except ImportError:
        print("❌ Flask no está instalado globalmente")
        print("   Por favor, crea y activa el virtualenv primero")

# Cambiar al directorio del proyecto
try:
    os.chdir(PROJECT_PATH)
    print(f"✅ Directorio cambiado a: {os.getcwd()}")
except Exception as e:
    print(f"⚠️ Error cambiando directorio: {e}")

# Importar la aplicación
try:
    from app import application
    print("✅ Aplicación importada correctamente")
    
    # Verificar que la aplicación sea válida
    if hasattr(application, 'wsgi_app'):
        print("✅ Aplicación WSGI válida")
    else:
        print("⚠️ La aplicación puede no ser compatible con WSGI")
        
except ImportError as e:
    print(f"❌ Error importando app.py: {e}")
    print("\n📋 POSIBLES CAUSAS:")
    print("   1. El archivo app.py no existe en el directorio")
    print("   2. Hay errores de sintaxis en app.py")
    print("   3. Faltan dependencias en el virtualenv")
    print("\n🔍 VERIFICACIÓN:")
    print(f"   • Directorio actual: {os.getcwd()}")
    print(f"   • Archivos en el directorio: {os.listdir('.')}")
    print(f"   • Python path: {sys.path}")
    raise

except Exception as e:
    print(f"❌ Error inesperado: {e}")
    print("\n📋 DETALLES DEL ERROR:")
    traceback.print_exc()
    raise

# Configuración adicional para manejo de archivos estáticos
# (PythonAnywhere maneja esto automáticamente en la configuración web)

print("\n" + "="*50)
print("🚀 APLICACIÓN INICIADA CORRECTAMENTE")
print("="*50)