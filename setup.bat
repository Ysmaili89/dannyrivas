@echo off
title Configuración del Ministerio Jhonatan Danny Rivas
color 0A

:: ============================================
:: SCRIPT DE CONFIGURACIÓN AUTOMÁTICA PARA WINDOWS
:: Ministerio Jhonatan Danny Rivas
:: Versión 2.0 - Optimizado para Render y Cloudinary
:: ============================================

echo ╔══════════════════════════════════════════════════════════╗
echo ║     Ministerio Jhonatan Danny Rivas - Instalador        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:: Verificar que estamos en el directorio correcto
if not exist "app.py" (
    echo ❌ ERROR: No se encuentra app.py en el directorio actual
    echo    Por favor, ejecuta este script desde C:\BLOG
    echo    o desde la raíz del proyecto
    pause
    exit /b 1
)

echo ✅ Directorio verificado: %CD%
echo.

:: Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo    Por favor, instala Python 3.8 o superior desde python.org
    pause
    exit /b 1
)

:: Mostrar versión de Python
for /f "tokens=*" %%i in ('python --version') do set PY_VERSION=%%i
echo ✅ %PY_VERSION% detectado
echo.

:: Verificar versión de Python (mínimo 3.8)
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  ADVERTENCIA: Se recomienda Python 3.8 o superior
    echo    Versión actual: %PY_VERSION%
    echo    Continuando de todas formas...
    echo.
)

:: Crear entorno virtual si no existe
if not exist "venv\" (
    echo 📦 Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo ✅ Entorno virtual creado
) else (
    echo ✅ Entorno virtual ya existe
)
echo.

:: Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo ✅ Entorno virtual activado
echo.

:: Actualizar pip
echo 📦 Actualizando pip...
python -m pip install --upgrade pip >nul 2>&1
echo ✅ Pip actualizado
echo.

:: Instalar dependencias desde requirements.txt si existe
if exist "requirements.txt" (
    echo 📦 Instalando dependencias desde requirements.txt...
    echo    Esto puede tomar varios minutos...
    echo.
    pip install -r requirements.txt
) else (
    echo 📦 Instalando dependencias básicas...
    echo.
    
    :: Instalar dependencias principales
    echo    ⚙️  Instalando Flask y extensiones...
    pip install flask==2.3.3 flask-login==0.6.2 flask-sqlalchemy==3.0.5 flask-wtf==1.1.1
    
    echo    ⚙️  Instalando utilidades...
    pip install werkzeug==2.3.7 email-validator==2.0.0 python-dotenv==1.0.0
    
    echo    ⚙️  Instalando Cloudinary para almacenamiento persistente...
    pip install cloudinary==1.36.0
    
    echo    ⚙️  Instalando base de datos PostgreSQL...
    pip install psycopg2-binary==2.9.9
    
    echo    ⚙️  Instalando Gunicorn para producción...
    pip install gunicorn==21.2.0
    
    echo    ⚙️  Instalando Redis para caché...
    pip install redis==5.0.1
    
    echo    ⚙️  Instalando Pillow para procesamiento de imágenes...
    pip install Pillow==10.1.0
)

:: Verificar instalación
if errorlevel 1 (
    echo ❌ ERROR: Hubo problemas durante la instalación
    echo    Revisa los mensajes de error arriba
    pause
    exit /b 1
)

echo.
echo ✅ Todas las dependencias instaladas correctamente
echo.

:: Crear carpetas necesarias si no existen
echo 📁 Verificando estructura de carpetas...

if not exist "static\" mkdir static
if not exist "static\css\" mkdir static\css
if not exist "static\js\" mkdir static\js
if not exist "static\images\" mkdir static\images
if not exist "static\uploads\" mkdir static\uploads
if not exist "static\uploads\videos\" mkdir static\uploads\videos
if not exist "static\uploads\images\" mkdir static\uploads\images
if not exist "static\uploads\gallery\" mkdir static\uploads\gallery
if not exist "templates\" mkdir templates
if not exist "templates\admin\" mkdir templates\admin

:: Crear archivo .gitkeep en carpetas vacías
echo ⚙️  Creando archivos .gitkeep para mantener carpetas en Git...
echo. > "static\uploads\.gitkeep" 2>nul
echo. > "static\uploads\videos\.gitkeep" 2>nul
echo. > "static\uploads\images\.gitkeep" 2>nul
echo. > "static\uploads\gallery\.gitkeep" 2>nul

echo ✅ Estructura de carpetas verificada
echo.

:: Crear archivo .env de ejemplo si no existe
if not exist ".env" (
    echo 📝 Creando archivo .env de ejemplo...
    (
        echo # Configuración para desarrollo local
        echo FLASK_ENV=development
        echo FLASK_DEBUG=1
        echo SECRET_KEY=clave-segura-para-desarrollo-123
        echo.
        echo # Base de datos (descomentar para PostgreSQL local)
        echo # DATABASE_URL=postgresql://usuario:password@localhost/ministerio_db
        echo.
        echo # Cloudinary (OBLIGATORIO PARA PRODUCCIÓN)
        echo # CLOUDINARY_CLOUD_NAME=tu_cloud_name
        echo # CLOUDINARY_API_KEY=tu_api_key
        echo # CLOUDINARY_API_SECRET=tu_api_secret
    ) > .env
    echo ✅ Archivo .env creado
) else (
    echo ✅ Archivo .env ya existe
)
echo.

:: Mostrar resumen
echo ╔══════════════════════════════════════════════════════════╗
echo ║                 INSTALACIÓN COMPLETADA                   ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 📋 RESUMEN:
echo   📁 Directorio: %CD%
echo   🐍 Python: %PY_VERSION%
echo   📦 Entorno virtual: venv\
echo   🔧 Estado: ✅ Listo para usar
echo.
echo 🚀 COMANDOS ÚTILES:
echo   • Activar entorno: venv\Scripts\activate
echo   • Iniciar app: python app.py
echo   • Ver dependencias: pip list
echo   • Actualizar req: pip freeze ^> requirements.txt
echo.
echo 🌐 PARA PRODUCCIÓN EN RENDER:
echo   1. Configura las variables de entorno en Render:
echo      - DATABASE_URL (PostgreSQL)
echo      - CLOUDINARY_CLOUD_NAME
echo      - CLOUDINARY_API_KEY
echo      - CLOUDINARY_API_SECRET
echo      - SECRET_KEY
echo.
echo   2. Los archivos se guardarán en Cloudinary (no se perderán)
echo.
echo ⚠️  IMPORTANTE:
echo   • Cambia la contraseña del admin en producción
echo   • Configura Cloudinary para persistencia de archivos
echo   • Revisa el archivo .env con tus credenciales
echo.
echo Presiona cualquier tecla para salir...
pause >nul

:: Desactivar entorno virtual (opcional)
call deactivate >nul 2>&1

exit /b 0