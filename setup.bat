#!/bin/bash
# Script de configuración para Linux/Mac

echo "============================================"
echo "Ministerio Jhonatan Danny Rivas - Instalador"
echo "============================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

PY_VERSION=$(python3 --version)
echo "✅ $PY_VERSION detectado"
echo ""

# Crear entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "✅ Entorno virtual ya existe"
fi
echo ""

# Activar entorno
echo "🔧 Activando entorno virtual..."
source venv/bin/activate
echo "✅ Entorno virtual activado"
echo ""

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip actualizado"
echo ""

# Instalar dependencias
if [ -f "requirements.txt" ]; then
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt no encontrado"
    echo "📦 Instalando dependencias básicas..."
    pip install Flask Flask-Login Flask-SQLAlchemy Flask-WTF
    pip install python-dotenv cloudinary gunicorn
    pip freeze > requirements.txt
    echo "✅ requirements.txt creado"
fi
echo ""

# Crear carpetas
echo "📁 Creando estructura de carpetas..."
mkdir -p static/{css,js,images,uploads/{videos,images,gallery}}
mkdir -p templates/admin
mkdir -p instance
touch static/uploads/.gitkeep
echo "✅ Carpetas creadas"
echo ""

# Crear .env
if [ ! -f ".env" ]; then
    echo "📝 Creando archivo .env..."
    cat > .env << EOF
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=clave-segura-para-desarrollo-123-cambiame
DATABASE_URL=sqlite:///instance/app.db
EOF
    echo "✅ .env creado"
fi
echo ""

echo "============================================"
echo "✅ INSTALACIÓN COMPLETADA"
echo "============================================"
echo ""
echo "📋 Para iniciar la app:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 Para producción en Render:"
echo "   Configura las variables de entorno en Render"
echo "============================================"