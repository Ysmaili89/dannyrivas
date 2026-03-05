# Este archivo va en /var/www/tuusuario_pythonanywhere_com_wsgi.py
# O lo configuras desde la web de PythonAnywhere

import sys
import os

# ¡CAMBIA ESTA RUTA! - Debe ser la ruta donde subiste tus archivos
path = '/home/tu_usuario/ministerio'
if path not in sys.path:
    sys.path.append(path)

# Importar la aplicación
from app import app as application

# ¡NO CAMBIES NADA MÁS!