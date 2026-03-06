"""
app.py - Aplicación principal del Ministerio Jhonatan Danny Rivas
VERSIÓN COMPLETA PARA PYTHONANYWHERE CON SQLITE
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import sys
import platform
import json
import re
import traceback
from functools import wraps
from urllib.parse import urlparse
import time

# Verificar dependencias
try:
    from flask_sqlalchemy import SQLAlchemy
    from flask_wtf.csrf import CSRFProtect
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Instala: pip install -r requirements.txt")
    sys.exit(1)

# ==================== CONFIGURACIÓN ====================
app = Flask(__name__)

# Directorio base
basedir = os.path.abspath(os.path.dirname(__file__))

# Seguridad
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cambia-esta-clave-en-produccion-123!')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False  # PythonAnywhere
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ==================== BASE DE DATOS SQLITE ====================
# Crear directorio instance si no existe
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/Ysmailin89/dannyrivas/instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_timeout': 30,
}

print(f"📁 Base de datos SQLite: {db_path}")

# ==================== CARPETAS DE SUBIDA ====================
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER_VIDEOS'] = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')
app.config['UPLOAD_FOLDER_IMAGES'] = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
app.config['UPLOAD_FOLDER_GALLERY'] = os.path.join(app.config['UPLOAD_FOLDER'], 'gallery')

# Crear todas las carpetas
for folder in [app.config['UPLOAD_FOLDER'], 
               app.config['UPLOAD_FOLDER_VIDEOS'], 
               app.config['UPLOAD_FOLDER_IMAGES'], 
               app.config['UPLOAD_FOLDER_GALLERY']]:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ Carpeta: {folder}")

# ==================== INICIALIZAR EXTENSIONES ====================
db = SQLAlchemy(app)
# csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'iniciar_sesion'
login_manager.login_message = 'Por favor inicia sesión para acceder al panel de administración.'
login_manager.login_message_category = 'info'

# ==================== CONFIGURACIONES DE SEGURIDAD ====================
ALLOWED_REDIRECT_DOMAINS = {
    'youtube.com', 'www.youtube.com', 'youtu.be',
    'facebook.com', 'www.facebook.com', 'fb.com',
    'instagram.com', 'www.instagram.com',
    'tiktok.com', 'www.tiktok.com',
    'twitter.com', 'www.twitter.com', 'x.com',
    'linkedin.com', 'www.linkedin.com',
    'wa.me', 'api.whatsapp.com', 'web.whatsapp.com',
    'paypal.com', 'www.paypal.com'
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mkv'}
ALLOWED_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEOS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# ==================== FUNCIONES UTILITARIAS ====================
def allowed_file(filename, allowed_types=None):
    if allowed_types is None:
        allowed_types = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_types

def allowed_image(filename):
    return allowed_file(filename, ALLOWED_IMAGES)

def allowed_video(filename):
    return allowed_file(filename, ALLOWED_VIDEOS)

def generar_nombre_unico(directorio, nombre_base, extension):
    """Genera nombre único para archivos"""
    timestamp = int(datetime.now().timestamp())
    filename = secure_filename(f"{nombre_base}_{timestamp}.{extension}")
    
    contador = 1
    ruta_completa = os.path.join(directorio, filename)
    while os.path.exists(ruta_completa):
        filename = secure_filename(f"{nombre_base}_{timestamp}_{contador}.{extension}")
        ruta_completa = os.path.join(directorio, filename)
        contador += 1
    
    return filename

def es_url_segura(url):
    """Valida URLs para redirecciones seguras"""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return True
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        for allowed in ALLOWED_REDIRECT_DOMAINS:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
        return False
    except Exception:
        return False

def validar_whatsapp(numero):
    """Valida número de WhatsApp"""
    if not numero:
        return None
    numero_limpio = re.sub(r'[^\d+]', '', numero)
    if numero_limpio.count('+') > 1:
        return None
    if '+' in numero_limpio and not numero_limpio.startswith('+'):
        return None
    numero_digitos = numero_limpio.replace('+', '')
    if not numero_digitos.isdigit() or len(numero_digitos) < 10 or len(numero_digitos) > 15:
        return None
    return numero_digitos

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder.', 'warning')
            return redirect(url_for('iniciar_sesion'))
        if not current_user.es_admin:
            flash('No tienes permisos para acceder a esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== MODELOS ====================
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)
    es_editor = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    ultimo_acceso = db.Column(db.DateTime)
    color = db.Column(db.String(20), default='#D4AF37')
    nombre_completo = db.Column(db.String(100))
    avatar = db.Column(db.String(500))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(50), default='fas fa-folder')
    color = db.Column(db.String(20), default='#D4AF37')
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    videos = db.relationship('Video', back_populates='categoria_rel', lazy='dynamic')

class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    youtube_url = db.Column(db.String(500), nullable=True)
    archivo = db.Column(db.String(500), nullable=True)
    thumbnail = db.Column(db.String(500))
    thumbnail_auto = db.Column(db.Boolean, default=True)
    thumbnail_upload = db.Column(db.Boolean, default=False)
    duracion = db.Column(db.String(20))
    vistas = db.Column(db.Integer, default=0)
    destacado = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(20), default='publicado')
    fecha_publicacion = db.Column(db.DateTime, default=datetime.now)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    categoria_rel = db.relationship('Categoria', back_populates='videos')

    __table_args__ = (
        db.Index('idx_video_estado', 'estado'),
        db.Index('idx_video_destacado', 'destacado'),
        db.Index('idx_video_fecha', 'fecha_publicacion'),
    )

    @property
    def url_video(self):
        if self.archivo:
            return f'/static/uploads/videos/{self.archivo}'
        return None

    @property
    def url_thumbnail(self):
        if self.thumbnail:
            return f'/static/uploads/images/{self.thumbnail}'
        return '/static/images/placeholder.jpg'

    @property
    def youtube_id(self):
        if self.youtube_url:
            match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([^&?/]+)', self.youtube_url)
            return match.group(1) if match else None
        return None

class Short(db.Model):
    __tablename__ = 'shorts'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    youtube_url = db.Column(db.String(500), nullable=True)
    video = db.Column(db.String(500), nullable=True)
    thumbnail = db.Column(db.String(500))
    thumbnail_auto = db.Column(db.Boolean, default=True)
    thumbnail_upload = db.Column(db.Boolean, default=False)
    duracion = db.Column(db.String(20))
    vistas = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='publicado')
    fecha_publicacion = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_short_estado', 'estado'),
        db.Index('idx_short_fecha', 'fecha_publicacion'),
    )

    @property
    def url_video(self):
        if self.video:
            return f'/static/uploads/videos/{self.video}'
        return None

    @property
    def url_thumbnail(self):
        if self.thumbnail:
            return f'/static/uploads/images/{self.thumbnail}'
        return '/static/images/placeholder.jpg'

    @property
    def youtube_id(self):
        if self.youtube_url:
            match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([^&?/]+)', self.youtube_url)
            return match.group(1) if match else None
        return None

class Galeria(db.Model):
    __tablename__ = 'galeria'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    archivo = db.Column(db.String(500), nullable=True)
    url_externa = db.Column(db.String(500), nullable=True)
    es_url = db.Column(db.Boolean, default=False)
    creditos = db.Column(db.String(200))
    categoria = db.Column(db.String(50), default='eventos')
    fecha_evento = db.Column(db.DateTime)
    fecha_subida = db.Column(db.DateTime, default=datetime.now)
    destacada = db.Column(db.Boolean, default=False)
    orden = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.Index('idx_galeria_categoria', 'categoria'),
        db.Index('idx_galeria_destacada', 'destacada'),
        db.Index('idx_galeria_fecha', 'fecha_subida'),
    )

    @property
    def url_imagen(self):
        if self.url_externa:
            return self.url_externa
        elif self.archivo:
            return f'/static/uploads/gallery/{self.archivo}'
        return '/static/images/placeholder.jpg'

class Testimonio(db.Model):
    __tablename__ = 'testimonios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100))
    titulo = db.Column(db.String(200))
    texto = db.Column(db.Text, nullable=False)
    publicado = db.Column(db.Boolean, default=False)
    anonimo = db.Column(db.Boolean, default=False)
    consentimiento = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_testimonio_publicado', 'publicado'),
        db.Index('idx_testimonio_fecha', 'fecha'),
    )

class Oracion(db.Model):
    __tablename__ = 'oraciones'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100))
    pais = db.Column(db.String(100))
    peticion = db.Column(db.Text, nullable=False)
    urgencia = db.Column(db.String(20), default='normal')
    anonimo = db.Column(db.Boolean, default=False)
    compartir = db.Column(db.Boolean, default=False)
    respondida = db.Column(db.Boolean, default=False)
    notas_admin = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_oracion_respondida', 'respondida'),
        db.Index('idx_oracion_fecha', 'fecha'),
    )

class Contacto(db.Model):
    __tablename__ = 'contactos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    asunto = db.Column(db.String(200))
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    notas_admin = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_contacto_leido', 'leido'),
        db.Index('idx_contacto_fecha', 'fecha'),
    )

class Invitacion(db.Model):
    __tablename__ = 'invitaciones'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    iglesia = db.Column(db.String(200))
    fecha_evento = db.Column(db.DateTime)
    hora = db.Column(db.String(20))
    lugar = db.Column(db.String(200))
    tipo_evento = db.Column(db.String(50))
    personas = db.Column(db.Integer)
    expectativas = db.Column(db.Text)
    confirmada = db.Column(db.Boolean, default=False)
    notas_admin = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_invitacion_confirmada', 'confirmada'),
        db.Index('idx_invitacion_fecha', 'fecha_envio'),
    )

class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_suscripcion = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_newsletter_email', 'email'),
        db.Index('idx_newsletter_activo', 'activo'),
    )

class Donacion(db.Model):
    __tablename__ = 'donaciones'
    id = db.Column(db.Integer, primary_key=True)
    banco = db.Column(db.String(100))
    titular = db.Column(db.String(200))
    tipo_cuenta = db.Column(db.String(50))
    numero_cuenta = db.Column(db.String(50))
    email_paypal = db.Column(db.String(100))
    paypal_me = db.Column(db.String(100))
    mensaje_bienvenida = db.Column(db.Text)
    mensaje_agradecimiento = db.Column(db.Text)
    versiculo = db.Column(db.String(500))
    versiculo_referencia = db.Column(db.String(100))
    montos_sugeridos = db.Column(db.Text, default='[10,25,50,100,500]')
    facebook = db.Column(db.String(500))
    instagram = db.Column(db.String(500))
    youtube = db.Column(db.String(500))
    whatsapp = db.Column(db.String(20))

    @property
    def montos_lista(self):
        try:
            return json.loads(self.montos_sugeridos) if self.montos_sugeridos else [10, 25, 50, 100, 500]
        except:
            return [10, 25, 50, 100, 500]

class Configuracion(db.Model):
    __tablename__ = 'configuracion'
    id = db.Column(db.Integer, primary_key=True)
    sitio_titulo = db.Column(db.String(200), default='Ministerio Jhonatan Danny Rivas')
    sitio_descripcion = db.Column(db.Text)
    sitio_keywords = db.Column(db.String(500))
    sitio_idioma = db.Column(db.String(10), default='es')
    sitio_zona_horaria = db.Column(db.String(50), default='America/Santo_Domingo')
    logo = db.Column(db.String(500))
    videos_por_pagina = db.Column(db.Integer, default=12)
    shorts_por_pagina = db.Column(db.Integer, default=8)
    comentarios_habilitados = db.Column(db.Boolean, default=True)
    videos_destacados = db.Column(db.Boolean, default=True)
    categorias_orden = db.Column(db.String(20), default='nombre')
    facebook_url = db.Column(db.String(500))
    instagram_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))
    tiktok_url = db.Column(db.String(500))
    twitter_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    live_tiktok_url = db.Column(db.String(500))
    email_contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    latitud = db.Column(db.String(20))
    longitud = db.Column(db.String(20))
    modo_mantenimiento = db.Column(db.Boolean, default=False)
    registro_abierto = db.Column(db.Boolean, default=True)
    youtube_api_key = db.Column(db.String(200))
    recaptcha_key = db.Column(db.String(200))
    backup_frecuencia = db.Column(db.String(20), default='semanal')

    @property
    def url_logo(self):
        if self.logo:
            return f'/static/uploads/images/{self.logo}'
        return None

# ==================== FUNCIONES DE INICIALIZACIÓN ====================
def ahora():
    return datetime.now()

app.jinja_env.globals.update(ahora=ahora)

# Cache para configuración
_config_cache = None
_config_cache_time = 0
_CONFIG_CACHE_TTL = 60

@app.context_processor
def inject_config():
    global _config_cache, _config_cache_time
    try:
        current_time = time.time()
        if _config_cache is None or (current_time - _config_cache_time) > _CONFIG_CACHE_TTL:
            config_db = Configuracion.query.first()
            if config_db:
                _config_cache = {
                    'sitio_titulo': config_db.sitio_titulo or 'Ministerio Jhonatan Danny Rivas',
                    'sitio_descripcion': config_db.sitio_descripcion or '',
                    'logo': config_db.url_logo or '',
                    'facebook_url': config_db.facebook_url or '',
                    'instagram_url': config_db.instagram_url or '',
                    'youtube_url': config_db.youtube_url or '',
                    'tiktok_url': config_db.tiktok_url or '',
                    'twitter_url': config_db.twitter_url or '',
                    'linkedin_url': config_db.linkedin_url or '',
                    'live_tiktok_url': config_db.live_tiktok_url or '',
                    'email_contacto': config_db.email_contacto or 'info@jhonatandannyrivas.com',
                    'telefono': config_db.telefono or '+1 809-555-1234',
                    'whatsapp': config_db.whatsapp or '',
                    'direccion': config_db.direccion or 'Santo Domingo, República Dominicana',
                    'videos_por_pagina': config_db.videos_por_pagina or 12,
                    'shorts_por_pagina': config_db.shorts_por_pagina or 8,
                }
            else:
                _config_cache = {}
            _config_cache_time = current_time
        return {'config': _config_cache}
    except Exception as e:
        print(f"⚠️ Error en config: {e}")
        return {'config': {}}

def init_db():
    """Inicializa la base de datos con datos por defecto"""
    try:
        db.create_all()
        print("✅ Tablas creadas")
        
        # Usuario admin por defecto
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                email='admin@jhonatandannyrivas.com',
                es_admin=True,
                activo=True,
                nombre_completo='Administrador'
            )
            admin.set_password('admin123')  # ¡CAMBIA ESTO!
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin creado: admin / admin123')
        
        # Configuración por defecto
        if not Configuracion.query.first():
            config = Configuracion(
                sitio_titulo='Ministerio Jhonatan Danny Rivas',
                sitio_descripcion='Predicando el evangelio de Jesucristo con poder y autoridad',
                email_contacto='info@jhonatandannyrivas.com',
                telefono='+1 809-555-1234',
                direccion='Santo Domingo, República Dominicana',
                facebook_url='https://www.facebook.com/share/1CbPDerCJ3/',
                instagram_url='https://www.instagram.com/rivasjonathanoficial',
                youtube_url='https://youtube.com/@jhonatanrivasoficial4487',
                tiktok_url='https://www.tiktok.com/@evangelistajhonat8',
                whatsapp='18099158969'
            )
            db.session.add(config)
            db.session.commit()
            print('✅ Configuración creada')
        
        # Categorías por defecto
        if Categoria.query.count() == 0:
            categorias = [
                {'nombre': 'Predicaciones', 'slug': 'predicaciones', 'icono': 'fas fa-cross', 'color': '#D4AF37'},
                {'nombre': 'Estudios Bíblicos', 'slug': 'estudios-biblicos', 'icono': 'fas fa-bible', 'color': '#2E7D32'},
                {'nombre': 'Devocionales', 'slug': 'devocionales', 'icono': 'fas fa-pray', 'color': '#1565C0'},
            ]
            for cat in categorias:
                cat['descripcion'] = f'Contenido de {cat["nombre"]}'
                db.session.add(Categoria(**cat))
            db.session.commit()
            print('✅ Categorías creadas')
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()

# ==================== VALIDACIONES ====================
def validar_youtube_url_unica(youtube_url, exclude_id=None, tipo='video'):
    if not youtube_url:
        return True, None
    video_query = Video.query.filter_by(youtube_url=youtube_url)
    if exclude_id and tipo == 'video':
        video_query = video_query.filter(Video.id != exclude_id)
    if video_query.first():
        return False, "❌ URL de YouTube ya registrada en otro video"
    short_query = Short.query.filter_by(youtube_url=youtube_url)
    if exclude_id and tipo == 'short':
        short_query = short_query.filter(Short.id != exclude_id)
    if short_query.first():
        return False, "❌ URL de YouTube ya registrada en un short"
    return True, None

def validar_url_externa_unica(url, exclude_id=None):
    if not url:
        return True, None
    query = Galeria.query.filter_by(url_externa=url)
    if exclude_id:
        query = query.filter(Galeria.id != exclude_id)
    if query.first():
        return False, "❌ URL ya registrada en otra imagen"
    return True, None

# ==================== RUTAS PÚBLICAS ====================
@app.route('/')
def index():
    try:
        pagina_videos = request.args.get('page_videos', 1, type=int)
        videos = Video.query.filter_by(estado='publicado')\
            .order_by(Video.fecha_publicacion.desc())\
            .limit(12).all()
        shorts = Short.query.filter_by(estado='publicado')\
            .order_by(Short.fecha_publicacion.desc())\
            .limit(8).all()
        return render_template('index.html', videos=videos, shorts=shorts)
    except Exception as e:
        print(f"Error en index: {e}")
        return render_template('index.html', videos=[], shorts=[])

@app.route('/video')
def video():
    try:
        pagina = request.args.get('page', 1, type=int)
        videos_paginados = Video.query.filter_by(estado='publicado')\
            .order_by(Video.fecha_publicacion.desc())\
            .paginate(page=pagina, per_page=12, error_out=False)
        categorias = Categoria.query.all()
        return render_template('video.html',
                             videos=videos_paginados.items,
                             categorias=categorias,
                             pagina_actual=pagina,
                             total_paginas=videos_paginados.pages)
    except Exception as e:
        print(f"Error en video: {e}")
        return render_template('video.html', videos=[])

@app.route('/short')
def short():
    try:
        pagina = request.args.get('page', 1, type=int)
        shorts_paginados = Short.query.filter_by(estado='publicado')\
            .order_by(Short.fecha_publicacion.desc())\
            .paginate(page=pagina, per_page=12, error_out=False)
        return render_template('short.html',
                             shorts=shorts_paginados.items,
                             pagina_actual=pagina,
                             total_paginas=shorts_paginados.pages)
    except Exception as e:
        print(f"Error en short: {e}")
        return render_template('short.html', shorts=[])

@app.route('/ver_video/<int:id>')
def ver_video(id):
    try:
        video = Video.query.get_or_404(id)
        video.vistas = (video.vistas or 0) + 1
        db.session.commit()
        relacionados = Video.query.filter(
            Video.categoria_id == video.categoria_id,
            Video.id != video.id,
            Video.estado == 'publicado'
        ).order_by(Video.fecha_publicacion.desc()).limit(6).all()
        return render_template('ver_video.html', video=video, relacionados=relacionados)
    except Exception as e:
        print(f"Error: {e}")
        flash('Video no encontrado', 'error')
        return redirect(url_for('video'))

@app.route('/ver_short/<int:id>')
def ver_short(id):
    try:
        short = Short.query.get_or_404(id)
        short.vistas = (short.vistas or 0) + 1
        db.session.commit()
        relacionados = Short.query.filter(
            Short.id != short.id,
            Short.estado == 'publicado'
        ).order_by(Short.fecha_publicacion.desc()).limit(6).all()
        return render_template('ver_short.html', short=short, relacionados=relacionados)
    except Exception as e:
        print(f"Error: {e}")
        flash('Short no encontrado', 'error')
        return redirect(url_for('short'))

@app.route('/categoria')
def categoria():
    try:
        categorias = Categoria.query.order_by(Categoria.nombre).all()
        return render_template('categoria.html', categorias=categorias)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('categoria.html', categorias=[])

@app.route('/categoria/<slug>')
def categoria_detalle(slug):
    try:
        categoria = Categoria.query.filter_by(slug=slug).first_or_404()
        pagina = request.args.get('page', 1, type=int)
        videos_paginados = Video.query.filter_by(
            categoria_id=categoria.id, estado='publicado'
        ).order_by(Video.fecha_publicacion.desc())\
         .paginate(page=pagina, per_page=12, error_out=False)
        return render_template('categoria_detalle.html',
                             categoria=categoria,
                             videos=videos_paginados.items,
                             pagina_actual=pagina,
                             total_paginas=videos_paginados.pages)
    except Exception as e:
        print(f"Error: {e}")
        flash('Categoría no encontrada', 'error')
        return redirect(url_for('categoria'))

@app.route('/oracion', methods=['GET', 'POST'])
def oracion():
    if request.method == 'POST':
        try:
            oracion = Oracion(
                nombre=request.form.get('nombre', '').strip()[:100],
                email=request.form.get('email', '').strip()[:100],
                pais=request.form.get('pais', '').strip()[:100],
                peticion=request.form.get('peticion', '').strip(),
                urgencia=request.form.get('urgencia', 'normal'),
                anonimo=request.form.get('anonimo') == 'on',
                compartir=request.form.get('compartir') == 'on'
            )
            db.session.add(oracion)
            db.session.commit()
            flash('¡Tu petición ha sido enviada! Dios te bendiga.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al enviar: {str(e)}', 'error')
        return redirect(url_for('oracion'))
    return render_template('oracion.html')

@app.route('/testimonio', methods=['GET', 'POST'])
def testimonio():
    if request.method == 'POST':
        try:
            testimonio = Testimonio(
                nombre=request.form.get('nombre', '').strip()[:100],
                email=request.form.get('email', '').strip()[:100],
                ciudad=request.form.get('ciudad', '').strip()[:100],
                titulo=request.form.get('titulo', '').strip()[:200],
                texto=request.form.get('testimonio', '').strip(),
                consentimiento=request.form.get('consentimiento') == 'on',
                publicado=False
            )
            db.session.add(testimonio)
            db.session.commit()
            flash('¡Gracias por compartir tu testimonio!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al enviar: {str(e)}', 'error')
        return redirect(url_for('testimonio'))
    testimonios = Testimonio.query.filter_by(publicado=True).order_by(Testimonio.fecha.desc()).all()
    return render_template('testimonio.html', testimonios=testimonios)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        try:
            contacto = Contacto(
                nombre=request.form.get('nombre', '').strip()[:100],
                email=request.form.get('email', '').strip()[:100],
                telefono=request.form.get('telefono', '').strip()[:20],
                asunto=request.form.get('asunto', '').strip()[:200],
                mensaje=request.form.get('mensaje', '').strip()
            )
            db.session.add(contacto)
            db.session.commit()
            flash('¡Mensaje enviado! Te responderemos pronto.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al enviar: {str(e)}', 'error')
        return redirect(url_for('contacto'))
    return render_template('contacto.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if request.method == 'POST':
        try:
            fecha_str = request.form.get('fecha')
            fecha_evento = datetime.strptime(fecha_str, '%Y-%m-%d') if fecha_str else None
            invitacion = Invitacion(
                nombre=request.form.get('nombre', '').strip()[:100],
                email=request.form.get('email', '').strip()[:100],
                telefono=request.form.get('telefono', '').strip()[:20],
                iglesia=request.form.get('iglesia', '').strip()[:200],
                fecha_evento=fecha_evento,
                hora=request.form.get('hora', '').strip()[:20],
                lugar=request.form.get('lugar', '').strip()[:200],
                tipo_evento=request.form.get('tipo_evento', '').strip()[:50],
                personas=request.form.get('personas', type=int),
                expectativas=request.form.get('expectativas', '').strip()
            )
            db.session.add(invitacion)
            db.session.commit()
            flash('¡Solicitud enviada! Te contactaremos.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al enviar: {str(e)}', 'error')
        return redirect(url_for('agenda'))
    return render_template('agenda.html')

@app.route('/galeria')
def galeria():
    try:
        imagenes = Galeria.query.order_by(
            Galeria.destacada.desc(), 
            Galeria.fecha_subida.desc()
        ).all()
        return render_template('galeria.html', imagenes=imagenes)
    except Exception as e:
        print(f"Error en galería: {e}")
        return render_template('galeria.html', imagenes=[])

@app.route('/donar')
def donar():
    try:
        config = Donacion.query.first()
        return render_template('donar.html', config=config)
    except Exception as e:
        print(f"Error en donar: {e}")
        return render_template('donar.html', config=None)

@app.route('/buscar')
def buscar():
    query = request.args.get('q', '').strip()
    resultados = []
    if query and len(query) >= 3:
        try:
            videos = Video.query.filter(
                db.or_(
                    Video.titulo.contains(query),
                    Video.descripcion.contains(query)
                )
            ).filter_by(estado='publicado').limit(20).all()
            resultados = videos
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            flash('Error al buscar', 'error')
    elif query:
        flash('Ingresa al menos 3 caracteres', 'warning')
    return render_template('buscar.html', query=query, resultados=resultados)

# ==================== NEWSLETTER ====================
@app.route('/suscribir', methods=['POST'])
def suscribir():
    email = request.form.get('email', '').strip().lower()
    if not email or '@' not in email:
        flash('Email válido requerido', 'error')
        return redirect(request.referrer or url_for('index'))
    try:
        existe = Newsletter.query.filter_by(email=email).first()
        if existe:
            if existe.activo:
                flash('Email ya suscrito', 'info')
            else:
                existe.activo = True
                db.session.commit()
                flash('¡Suscripción reactivada!', 'success')
        else:
            suscriptor = Newsletter(email=email)
            db.session.add(suscriptor)
            db.session.commit()
            flash('¡Gracias por suscribirte!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(request.referrer or url_for('index'))

# ==================== PÁGINAS LEGALES ====================
@app.route('/terminos')
def terminos():
    return render_template('terminos.html')

@app.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')

@app.route('/aviso-legal')
def aviso_legal():
    return render_template('aviso-legal.html')

@app.route('/accesibilidad')
def accesibilidad():
    return render_template('accesibilidad.html', current_date=datetime.now())

@app.route('/mapa-web')
def mapa_web():
    return render_template('mapa-web.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# ==================== REDIRECTS ====================
@app.route('/admin')
def admin_redirect():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('iniciar_sesion'))

@app.route('/youtube')
def youtube_redirect():
    config = Configuracion.query.first()
    if config and config.youtube_url:
        return redirect(config.youtube_url)
    return redirect('https://youtube.com')

@app.route('/facebook')
def facebook_redirect():
    config = Configuracion.query.first()
    if config and config.facebook_url:
        return redirect(config.facebook_url)
    return redirect('https://facebook.com')

@app.route('/instagram')
def instagram_redirect():
    config = Configuracion.query.first()
    if config and config.instagram_url:
        return redirect(config.instagram_url)
    return redirect('https://instagram.com')

@app.route('/tiktok')
def tiktok_redirect():
    config = Configuracion.query.first()
    if config and config.tiktok_url:
        return redirect(config.tiktok_url)
    return redirect('https://tiktok.com')

@app.route('/twitter')
def twitter_redirect():
    config = Configuracion.query.first()
    if config and config.twitter_url:
        return redirect(config.twitter_url)
    return redirect('https://twitter.com')

@app.route('/linkedin')
def linkedin_redirect():
    config = Configuracion.query.first()
    if config and config.linkedin_url:
        return redirect(config.linkedin_url)
    return redirect('https://linkedin.com')

@app.route('/whatsapp')
def whatsapp_redirect():
    config = Configuracion.query.first()
    if config and config.whatsapp:
        numero = validar_whatsapp(config.whatsapp)
        if numero:
            return redirect(f'https://wa.me/{numero}')
    flash('WhatsApp no configurado', 'warning')
    return redirect(url_for('contacto'))

# ==================== AUTENTICACIÓN ====================
@app.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        usuario = Usuario.query.filter_by(username=username, activo=True).first()
        if usuario and usuario.check_password(password):
            login_user(usuario, remember=remember)
            usuario.ultimo_acceso = datetime.now()
            db.session.commit()
            flash(f'¡Bienvenido {usuario.username}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('iniciar_sesion.html')

@app.route('/cerrar_sesion')
@login_required
def cerrar_sesion():
    logout_user()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('index'))

# ==================== ADMIN - DASHBOARD ====================
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        stats = {
            'total_oraciones': Oracion.query.count(),
            'oraciones_pendientes': Oracion.query.filter_by(respondida=False).count(),
            'total_testimonios': Testimonio.query.count(),
            'testimonios_pendientes': Testimonio.query.filter_by(publicado=False).count(),
            'total_contactos': Contacto.query.count(),
            'contactos_no_leidos': Contacto.query.filter_by(leido=False).count(),
            'total_invitaciones': Invitacion.query.count(),
            'invitaciones_pendientes': Invitacion.query.filter_by(confirmada=False).count(),
            'total_videos': Video.query.count(),
            'videos_publicados': Video.query.filter_by(estado='publicado').count(),
            'total_shorts': Short.query.count(),
            'shorts_publicados': Short.query.filter_by(estado='publicado').count(),
            'total_galeria': Galeria.query.count(),
            'total_newsletter': Newsletter.query.count(),
            'newsletter_activos': Newsletter.query.filter_by(activo=True).count(),
        }
        
        ultimas_oraciones = Oracion.query.order_by(Oracion.fecha.desc()).limit(5).all()
        ultimos_testimonios = Testimonio.query.order_by(Testimonio.fecha.desc()).limit(5).all()
        ultimos_contactos = Contacto.query.order_by(Contacto.fecha.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             ultimas_oraciones=ultimas_oraciones,
                             ultimos_testimonios=ultimos_testimonios,
                             ultimos_contactos=ultimos_contactos)
    except Exception as e:
        print(f"Error en dashboard: {e}")
        return render_template('admin/dashboard.html', stats={})

@app.route('/admin/perfil')
@login_required
def perfil():
    return render_template('admin/perfil.html', usuario=current_user)

# ==================== ADMIN - VIDEOS ====================
@app.route('/admin/videos')
@login_required
@admin_required
def lista_videos():
    try:
        pagina = request.args.get('page', 1, type=int)
        videos = Video.query.order_by(Video.fecha_publicacion.desc())\
            .paginate(page=pagina, per_page=20, error_out=False)
        categorias = Categoria.query.all()
        return render_template('admin/lista_videos.html',
                             videos=videos.items,
                             pagina_actual=pagina,
                             total_paginas=videos.pages,
                             categorias=categorias)
    except Exception as e:
        print(f"Error: {e}")
        flash('Error al cargar videos', 'error')
        return render_template('admin/lista_videos.html', videos=[])

@app.route('/admin/videos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_video():
    if request.method == 'POST':
        try:
            youtube_url = request.form.get('youtube_url', '').strip()
            if youtube_url:
                valido, msg = validar_youtube_url_unica(youtube_url, tipo='video')
                if not valido:
                    flash(msg, 'error')
                    return redirect(url_for('crear_video'))
            
            video = Video(
                titulo=request.form.get('titulo', '').strip(),
                descripcion=request.form.get('descripcion', '').strip(),
                youtube_url=youtube_url,
                duracion=request.form.get('duracion', '').strip(),
                categoria_id=request.form.get('categoria', type=int),
                estado=request.form.get('estado', 'borrador'),
                destacado=request.form.get('destacado') == 'on'
            )
            
            # Manejar thumbnail
            thumbnail_option = request.form.get('thumbnail_option', 'auto')
            if thumbnail_option == 'upload' and request.files.get('thumbnail'):
                file = request.files['thumbnail']
                if file and file.filename and allowed_image(file.filename):
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_IMAGES'], 'video_thumb', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    video.thumbnail = filename
                    video.thumbnail_upload = True
                    video.thumbnail_auto = False
            
            db.session.add(video)
            db.session.commit()
            flash('Video creado correctamente', 'success')
            return redirect(url_for('lista_videos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    categorias = Categoria.query.all()
    return render_template('admin/crear_video.html', categorias=categorias)

@app.route('/admin/videos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_video(id):
    video = Video.query.get_or_404(id)
    if request.method == 'POST':
        try:
            youtube_url = request.form.get('youtube_url', '').strip()
            if youtube_url and youtube_url != video.youtube_url:
                valido, msg = validar_youtube_url_unica(youtube_url, exclude_id=id, tipo='video')
                if not valido:
                    flash(msg, 'error')
                    return redirect(url_for('editar_video', id=id))
            
            video.titulo = request.form.get('titulo', '').strip()
            video.descripcion = request.form.get('descripcion', '').strip()
            video.youtube_url = youtube_url
            video.duracion = request.form.get('duracion', '').strip()
            video.categoria_id = request.form.get('categoria', type=int)
            video.estado = request.form.get('estado', 'borrador')
            video.destacado = request.form.get('destacado') == 'on'
            
            # Manejar thumbnail
            thumbnail_option = request.form.get('thumbnail_option', 'auto')
            if thumbnail_option == 'upload' and request.files.get('thumbnail') and request.files['thumbnail'].filename:
                file = request.files['thumbnail']
                if allowed_image(file.filename):
                    if video.thumbnail:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], video.thumbnail)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_IMAGES'], f'video_thumb_{id}', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    video.thumbnail = filename
                    video.thumbnail_upload = True
                    video.thumbnail_auto = False
            elif thumbnail_option == 'auto' and video.thumbnail_upload:
                if video.thumbnail:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], video.thumbnail)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                video.thumbnail = None
                video.thumbnail_upload = False
                video.thumbnail_auto = True
            
            db.session.commit()
            flash('Video actualizado', 'success')
            return redirect(url_for('lista_videos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    categorias = Categoria.query.all()
    return render_template('admin/crear_video.html', video=video, categorias=categorias)

@app.route('/admin/videos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_video(id):
    video = Video.query.get_or_404(id)
    try:
        if video.thumbnail:
            path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], video.thumbnail)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(video)
        db.session.commit()
        flash('Video eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_videos'))

# ==================== ADMIN - SHORTS ====================
@app.route('/admin/shorts')
@login_required
@admin_required
def lista_shorts():
    try:
        pagina = request.args.get('page', 1, type=int)
        shorts = Short.query.order_by(Short.fecha_publicacion.desc())\
            .paginate(page=pagina, per_page=20, error_out=False)
        return render_template('admin/lista_shorts.html',
                             shorts=shorts.items,
                             pagina_actual=pagina,
                             total_paginas=shorts.pages)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_shorts.html', shorts=[])

@app.route('/admin/shorts/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_short():
    if request.method == 'POST':
        try:
            youtube_url = request.form.get('youtube_url', '').strip()
            if youtube_url:
                valido, msg = validar_youtube_url_unica(youtube_url, tipo='short')
                if not valido:
                    flash(msg, 'error')
                    return redirect(url_for('crear_short'))
            
            short = Short(
                titulo=request.form.get('titulo', '').strip(),
                descripcion=request.form.get('descripcion', '').strip(),
                youtube_url=youtube_url,
                duracion=request.form.get('duracion', '').strip(),
                estado=request.form.get('estado', 'borrador')
            )
            
            # Video subido
            if request.files.get('video_file') and request.files['video_file'].filename:
                file = request.files['video_file']
                if allowed_video(file.filename):
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_VIDEOS'], 'short', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], filename))
                    short.video = filename
            
            # Thumbnail
            thumbnail_option = request.form.get('thumbnail_option', 'auto')
            if thumbnail_option == 'upload' and request.files.get('thumbnail'):
                file = request.files['thumbnail']
                if file and file.filename and allowed_image(file.filename):
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_IMAGES'], 'short_thumb', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    short.thumbnail = filename
                    short.thumbnail_upload = True
                    short.thumbnail_auto = False
            
            db.session.add(short)
            db.session.commit()
            flash('Short creado', 'success')
            return redirect(url_for('lista_shorts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/crear_short.html')

@app.route('/admin/shorts/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_short(id):
    short = Short.query.get_or_404(id)
    if request.method == 'POST':
        try:
            youtube_url = request.form.get('youtube_url', '').strip()
            if youtube_url and youtube_url != short.youtube_url:
                valido, msg = validar_youtube_url_unica(youtube_url, exclude_id=id, tipo='short')
                if not valido:
                    flash(msg, 'error')
                    return redirect(url_for('editar_short', id=id))
            
            short.titulo = request.form.get('titulo', '').strip()
            short.descripcion = request.form.get('descripcion', '').strip()
            short.youtube_url = youtube_url
            short.duracion = request.form.get('duracion', '').strip()
            short.estado = request.form.get('estado', 'borrador')
            
            # Video subido
            if request.files.get('video_file') and request.files['video_file'].filename:
                file = request.files['video_file']
                if allowed_video(file.filename):
                    if short.video:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], short.video)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_VIDEOS'], f'short_{id}', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], filename))
                    short.video = filename
            
            # Thumbnail
            thumbnail_option = request.form.get('thumbnail_option', 'auto')
            if thumbnail_option == 'upload' and request.files.get('thumbnail') and request.files['thumbnail'].filename:
                file = request.files['thumbnail']
                if allowed_image(file.filename):
                    if short.thumbnail:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], short.thumbnail)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_IMAGES'], f'short_thumb_{id}', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    short.thumbnail = filename
                    short.thumbnail_upload = True
                    short.thumbnail_auto = False
            elif thumbnail_option == 'auto' and short.thumbnail_upload:
                if short.thumbnail:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], short.thumbnail)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                short.thumbnail = None
                short.thumbnail_upload = False
                short.thumbnail_auto = True
            
            db.session.commit()
            flash('Short actualizado', 'success')
            return redirect(url_for('lista_shorts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/crear_short.html', short=short)

@app.route('/admin/shorts/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_short(id):
    short = Short.query.get_or_404(id)
    try:
        if short.video:
            path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], short.video)
            if os.path.exists(path):
                os.remove(path)
        if short.thumbnail:
            path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], short.thumbnail)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(short)
        db.session.commit()
        flash('Short eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_shorts'))

# ==================== ADMIN - CATEGORÍAS ====================
@app.route('/admin/categorias')
@login_required
@admin_required
def lista_categorias():
    try:
        categorias = Categoria.query.all()
        return render_template('admin/lista_categorias.html', categorias=categorias)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_categorias.html', categorias=[])

@app.route('/admin/categorias/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_categoria():
    if request.method == 'POST':
        try:
            categoria = Categoria(
                nombre=request.form.get('nombre', '').strip(),
                slug=request.form.get('slug', '').strip(),
                descripcion=request.form.get('descripcion', '').strip(),
                icono=request.form.get('icono', 'fas fa-folder'),
                color=request.form.get('color', '#D4AF37')
            )
            db.session.add(categoria)
            db.session.commit()
            flash('Categoría creada', 'success')
            return redirect(url_for('lista_categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/crear_categoria.html')

@app.route('/admin/categorias/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    if request.method == 'POST':
        try:
            categoria.nombre = request.form.get('nombre', '').strip()
            categoria.slug = request.form.get('slug', '').strip()
            categoria.descripcion = request.form.get('descripcion', '').strip()
            categoria.icono = request.form.get('icono', 'fas fa-folder')
            categoria.color = request.form.get('color', '#D4AF37')
            db.session.commit()
            flash('Categoría actualizada', 'success')
            return redirect(url_for('lista_categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/crear_categoria.html', categoria=categoria)

@app.route('/admin/categorias/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    try:
        if categoria.videos and categoria.videos.count() > 0:
            flash('No se puede eliminar: tiene videos asociados', 'error')
            return redirect(url_for('lista_categorias'))
        db.session.delete(categoria)
        db.session.commit()
        flash('Categoría eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_categorias'))

# ==================== ADMIN - TESTIMONIOS ====================
@app.route('/admin/testimonios')
@login_required
@admin_required
def lista_testimonios():
    try:
        pagina = request.args.get('page', 1, type=int)
        testimonios = Testimonio.query.order_by(Testimonio.fecha.desc())\
            .paginate(page=pagina, per_page=20, error_out=False)
        pendientes = Testimonio.query.filter_by(publicado=False).count()
        return render_template('admin/lista_testimonios.html',
                             testimonios=testimonios,
                             testimonios_pendientes=pendientes)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_testimonios.html', testimonios=[])

@app.route('/admin/testimonios/<int:id>/publicar', methods=['POST'])
@login_required
@admin_required
def publicar_testimonio(id):
    testimonio = Testimonio.query.get_or_404(id)
    testimonio.publicado = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/testimonios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_testimonio(id):
    testimonio = Testimonio.query.get_or_404(id)
    if request.method == 'POST':
        try:
            testimonio.nombre = request.form.get('nombre', '').strip()
            testimonio.email = request.form.get('email', '').strip()
            testimonio.ciudad = request.form.get('ciudad', '').strip()
            testimonio.titulo = request.form.get('titulo', '').strip()
            testimonio.texto = request.form.get('texto', '').strip()
            testimonio.publicado = request.form.get('publicado') == 'on'
            testimonio.anonimo = request.form.get('anonimo') == 'on'
            db.session.commit()
            flash('Testimonio actualizado', 'success')
            return redirect(url_for('lista_testimonios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/editar_testimonio.html', testimonio=testimonio)

@app.route('/admin/testimonios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_testimonio(id):
    testimonio = Testimonio.query.get_or_404(id)
    try:
        db.session.delete(testimonio)
        db.session.commit()
        flash('Testimonio eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_testimonios'))

# ==================== ADMIN - ORACIONES ====================
@app.route('/admin/oraciones')
@login_required
@admin_required
def lista_oraciones():
    try:
        pagina = request.args.get('page', 1, type=int)
        oraciones = Oracion.query.order_by(Oracion.fecha.desc())\
            .paginate(page=pagina, per_page=20, error_out=False)
        return render_template('admin/lista_oraciones.html', oraciones=oraciones)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_oraciones.html', oraciones=[])

@app.route('/admin/oraciones/<int:id>/responder', methods=['POST'])
@login_required
@admin_required
def marcar_oracion_respondida(id):
    oracion = Oracion.query.get_or_404(id)
    oracion.respondida = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/oraciones/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_oracion(id):
    oracion = Oracion.query.get_or_404(id)
    if request.method == 'POST':
        try:
            oracion.respondida = request.form.get('respondida') == 'on'
            oracion.notas_admin = request.form.get('notas_admin', '').strip()
            db.session.commit()
            flash('Petición actualizada', 'success')
            return redirect(url_for('lista_oraciones'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/editar_oracion.html', oracion=oracion)

@app.route('/admin/oraciones/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_oracion(id):
    oracion = Oracion.query.get_or_404(id)
    try:
        db.session.delete(oracion)
        db.session.commit()
        flash('Petición eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_oraciones'))

# ==================== ADMIN - CONTACTOS ====================
@app.route('/admin/contactos')
@login_required
@admin_required
def lista_contactos():
    try:
        pagina = request.args.get('page', 1, type=int)
        contactos = Contacto.query.order_by(Contacto.fecha.desc())\
            .paginate(page=pagina, per_page=20, error_out=False)
        no_leidos = Contacto.query.filter_by(leido=False).count()
        return render_template('admin/lista_contactos.html',
                             contactos=contactos,
                             no_leidos_count=no_leidos)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_contactos.html', contactos=[])

@app.route('/admin/contactos/<int:id>/leer', methods=['POST'])
@login_required
@admin_required
def marcar_contacto_leido(id):
    contacto = Contacto.query.get_or_404(id)
    contacto.leido = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/contactos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_contacto(id):
    contacto = Contacto.query.get_or_404(id)
    if request.method == 'POST':
        try:
            contacto.leido = request.form.get('leido') == 'on'
            contacto.notas_admin = request.form.get('notas_admin', '').strip()
            db.session.commit()
            flash('Contacto actualizado', 'success')
            return redirect(url_for('lista_contactos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/editar_contacto.html', contacto=contacto)

@app.route('/admin/contactos/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_contacto(id):
    contacto = Contacto.query.get_or_404(id)
    try:
        db.session.delete(contacto)
        db.session.commit()
        flash('Contacto eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_contactos'))

# ==================== ADMIN - INVITACIONES ====================
@app.route('/admin/invitaciones')
@login_required
@admin_required
def lista_invitaciones():
    try:
        pagina = request.args.get('page', 1, type=int)
        invitaciones = Invitacion.query.order_by(Invitacion.fecha_envio.desc())\
            .paginate(page=pagina, per_page=20, error_out=False)
        pendientes = Invitacion.query.filter_by(confirmada=False).count()
        return render_template('admin/lista_invitaciones.html',
                             invitaciones=invitaciones,
                             pendientes_count=pendientes)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_invitaciones.html', invitaciones=[])

@app.route('/admin/invitaciones/<int:id>/confirmar', methods=['POST'])
@login_required
@admin_required
def confirmar_invitacion(id):
    invitacion = Invitacion.query.get_or_404(id)
    invitacion.confirmada = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/invitaciones/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_invitacion(id):
    invitacion = Invitacion.query.get_or_404(id)
    if request.method == 'POST':
        try:
            invitacion.confirmada = request.form.get('confirmada') == 'on'
            invitacion.notas_admin = request.form.get('notas_admin', '').strip()
            db.session.commit()
            flash('Invitación actualizada', 'success')
            return redirect(url_for('lista_invitaciones'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/editar_invitacion.html', invitacion=invitacion)

@app.route('/admin/invitaciones/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_invitacion(id):
    invitacion = Invitacion.query.get_or_404(id)
    try:
        db.session.delete(invitacion)
        db.session.commit()
        flash('Invitación eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_invitaciones'))

# ==================== ADMIN - USUARIOS ====================
@app.route('/admin/usuarios')
@login_required
@admin_required
def lista_usuarios():
    try:
        usuarios = Usuario.query.all()
        return render_template('admin/lista_usuarios.html', usuarios=usuarios)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_usuarios.html', usuarios=[])

@app.route('/admin/usuarios/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    if request.method == 'POST':
        try:
            usuario = Usuario(
                username=request.form.get('username', '').strip(),
                email=request.form.get('email', '').strip(),
                es_admin=request.form.get('es_admin') == 'on',
                activo=True
            )
            usuario.set_password(request.form.get('password', ''))
            db.session.add(usuario)
            db.session.commit()
            flash('Usuario creado', 'success')
            return redirect(url_for('lista_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/crear_usuario.html')

@app.route('/admin/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        try:
            usuario.username = request.form.get('username', '').strip()
            usuario.email = request.form.get('email', '').strip()
            usuario.es_admin = request.form.get('es_admin') == 'on'
            if request.form.get('password'):
                usuario.set_password(request.form.get('password'))
            db.session.commit()
            flash('Usuario actualizado', 'success')
            return redirect(url_for('lista_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/editar_usuario.html', usuario=usuario)

@app.route('/admin/usuarios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(id):
    if id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('lista_usuarios'))
    usuario = Usuario.query.get_or_404(id)
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_usuarios'))

# ==================== ADMIN - NEWSLETTER ====================
@app.route('/admin/newsletter')
@login_required
@admin_required
def lista_newsletter():
    try:
        suscriptores = Newsletter.query.order_by(Newsletter.fecha_suscripcion.desc()).all()
        return render_template('admin/lista_newsletter.html', suscriptores=suscriptores)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_newsletter.html', suscriptores=[])

@app.route('/admin/newsletter/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_newsletter(id):
    suscriptor = Newsletter.query.get_or_404(id)
    suscriptor.activo = not suscriptor.activo
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/newsletter/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_newsletter(id):
    suscriptor = Newsletter.query.get_or_404(id)
    try:
        db.session.delete(suscriptor)
        db.session.commit()
        flash('Suscriptor eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_newsletter'))

# ==================== ADMIN - GALERÍA ====================
@app.route('/admin/galeria')
@login_required
@admin_required
def lista_galeria():
    try:
        pagina = request.args.get('page', 1, type=int)
        imagenes = Galeria.query.order_by(
            Galeria.destacada.desc(), 
            Galeria.fecha_subida.desc()
        ).paginate(page=pagina, per_page=12, error_out=False)
        return render_template('admin/lista_galeria.html',
                             imagenes=imagenes.items,
                             pagina_actual=pagina,
                             total_paginas=imagenes.pages)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin/lista_galeria.html', imagenes=[])

@app.route('/admin/galeria/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_imagen():
    if request.method == 'POST':
        try:
            usar_url = request.form.get('url_externa') == 'on'
            
            if usar_url:
                url = request.form.get('imagen_url', '').strip()
                if not url:
                    flash('URL requerida', 'error')
                    return redirect(url_for('crear_imagen'))
                
                valido, msg = validar_url_externa_unica(url)
                if not valido:
                    flash(msg, 'error')
                    return redirect(url_for('crear_imagen'))
                
                fecha_evento = None
                if request.form.get('fecha'):
                    fecha_evento = datetime.strptime(request.form.get('fecha'), '%Y-%m-%d')
                
                imagen = Galeria(
                    titulo=request.form.get('titulo', '').strip(),
                    descripcion=request.form.get('descripcion', '').strip(),
                    url_externa=url,
                    creditos=request.form.get('creditos', '').strip(),
                    es_url=True,
                    categoria=request.form.get('categoria', 'eventos'),
                    fecha_evento=fecha_evento,
                    destacada=request.form.get('destacada') == 'on'
                )
                db.session.add(imagen)
                db.session.commit()
                flash('Imagen agregada desde URL', 'success')
            else:
                archivo = request.files.get('archivo')
                if archivo and archivo.filename and allowed_image(archivo.filename):
                    extension = archivo.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_GALLERY'], 'galeria', extension)
                    archivo.save(os.path.join(app.config['UPLOAD_FOLDER_GALLERY'], filename))
                    
                    fecha_evento = None
                    if request.form.get('fecha'):
                        fecha_evento = datetime.strptime(request.form.get('fecha'), '%Y-%m-%d')
                    
                    imagen = Galeria(
                        titulo=request.form.get('titulo', '').strip(),
                        descripcion=request.form.get('descripcion', '').strip(),
                        archivo=filename,
                        es_url=False,
                        categoria=request.form.get('categoria', 'eventos'),
                        fecha_evento=fecha_evento,
                        destacada=request.form.get('destacada') == 'on'
                    )
                    db.session.add(imagen)
                    db.session.commit()
                    flash('Imagen subida correctamente', 'success')
                else:
                    flash('Archivo de imagen válido requerido', 'error')
                    return redirect(url_for('crear_imagen'))
            
            return redirect(url_for('lista_galeria'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/crear_imagen.html')

@app.route('/admin/galeria/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_imagen(id):
    imagen = Galeria.query.get_or_404(id)
    if request.method == 'POST':
        try:
            imagen.titulo = request.form.get('titulo', '').strip()
            imagen.descripcion = request.form.get('descripcion', '').strip()
            imagen.categoria = request.form.get('categoria', 'eventos')
            imagen.creditos = request.form.get('creditos', '').strip()
            
            if request.form.get('fecha'):
                imagen.fecha_evento = datetime.strptime(request.form.get('fecha'), '%Y-%m-%d')
            else:
                imagen.fecha_evento = None
            
            imagen.destacada = request.form.get('destacada') == 'on'
            
            usar_url = request.form.get('url_externa') == 'on'
            if usar_url:
                url = request.form.get('imagen_url', '').strip()
                if url and url != imagen.url_externa:
                    valido, msg = validar_url_externa_unica(url, exclude_id=id)
                    if not valido:
                        flash(msg, 'error')
                        return redirect(url_for('editar_imagen', id=id))
                    imagen.url_externa = url
                    imagen.es_url = True
                    if imagen.archivo:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_GALLERY'], imagen.archivo)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                        imagen.archivo = None
            else:
                archivo = request.files.get('archivo')
                if archivo and archivo.filename and allowed_image(archivo.filename):
                    if imagen.archivo and not imagen.es_url:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_GALLERY'], imagen.archivo)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    extension = archivo.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_GALLERY'], f'galeria_{id}', extension)
                    archivo.save(os.path.join(app.config['UPLOAD_FOLDER_GALLERY'], filename))
                    imagen.archivo = filename
                    imagen.es_url = False
                    imagen.url_externa = None
            
            db.session.commit()
            flash('Imagen actualizada', 'success')
            return redirect(url_for('lista_galeria'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    return render_template('admin/editar_imagen.html', imagen=imagen)

@app.route('/admin/galeria/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_imagen(id):
    imagen = Galeria.query.get_or_404(id)
    try:
        if not imagen.es_url and imagen.archivo:
            path = os.path.join(app.config['UPLOAD_FOLDER_GALLERY'], imagen.archivo)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(imagen)
        db.session.commit()
        flash('Imagen eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('lista_galeria'))

# ==================== ADMIN - DONACIONES ====================
@app.route('/admin/donaciones', methods=['GET', 'POST'])
@login_required
@admin_required
def configurar_donaciones():
    config = Donacion.query.first()
    if request.method == 'POST':
        try:
            if not config:
                config = Donacion()
            config.banco = request.form.get('banco', '').strip()
            config.titular = request.form.get('titular', '').strip()
            config.tipo_cuenta = request.form.get('tipo_cuenta', '').strip()
            config.numero_cuenta = request.form.get('numero_cuenta', '').strip()
            config.email_paypal = request.form.get('email_paypal', '').strip()
            config.paypal_me = request.form.get('paypal_me', '').strip()
            config.mensaje_bienvenida = request.form.get('mensaje_bienvenida', '').strip()
            config.mensaje_agradecimiento = request.form.get('mensaje_agradecimiento', '').strip()
            config.versiculo = request.form.get('versiculo', '').strip()
            config.versiculo_referencia = request.form.get('versiculo_referencia', '').strip()
            montos = request.form.getlist('montos[]')
            if montos:
                config.montos_sugeridos = json.dumps([int(m) for m in montos if m])
            config.facebook = request.form.get('facebook', '').strip()
            config.instagram = request.form.get('instagram', '').strip()
            config.youtube = request.form.get('youtube', '').strip()
            config.whatsapp = request.form.get('whatsapp', '').strip()
            if not config.id:
                db.session.add(config)
            db.session.commit()
            flash('Configuración guardada', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('configurar_donaciones'))
    return render_template('admin/configuracion_donaciones.html', config=config)

# ==================== ADMIN - CONFIGURACIÓN GENERAL ====================
@app.route('/admin/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    config = Configuracion.query.first()
    if request.method == 'POST':
        try:
            if not config:
                config = Configuracion()
                db.session.add(config)
            
            config.sitio_titulo = request.form.get('sitio_titulo', '').strip()
            config.sitio_descripcion = request.form.get('sitio_descripcion', '').strip()
            config.sitio_keywords = request.form.get('sitio_keywords', '').strip()
            config.email_contacto = request.form.get('email_contacto', '').strip()
            config.telefono = request.form.get('telefono', '').strip()
            config.whatsapp = request.form.get('whatsapp', '').strip()
            config.direccion = request.form.get('direccion', '').strip()
            config.videos_por_pagina = request.form.get('videos_por_pagina', 12, type=int)
            config.shorts_por_pagina = request.form.get('shorts_por_pagina', 8, type=int)
            
            # Redes sociales
            config.facebook_url = request.form.get('facebook_url', '').strip()
            config.instagram_url = request.form.get('instagram_url', '').strip()
            config.youtube_url = request.form.get('youtube_url', '').strip()
            config.tiktok_url = request.form.get('tiktok_url', '').strip()
            config.twitter_url = request.form.get('twitter_url', '').strip()
            config.linkedin_url = request.form.get('linkedin_url', '').strip()
            config.live_tiktok_url = request.form.get('live_tiktok_url', '').strip()
            
            # Logo
            if request.files.get('logo') and request.files['logo'].filename:
                file = request.files['logo']
                if allowed_image(file.filename):
                    if config.logo:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], config.logo)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    extension = file.filename.rsplit('.', 1)[1].lower()
                    filename = generar_nombre_unico(app.config['UPLOAD_FOLDER_IMAGES'], 'logo', extension)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    config.logo = filename
            
            db.session.commit()
            global _config_cache
            _config_cache = None
            flash('Configuración guardada', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('configuracion'))
    
    system_info = {
        'python_version': platform.python_version(),
        'flask_version': '2.3.3',
        'db_type': 'SQLite',
        'last_backup': 'Nunca'
    }
    return render_template('admin/configuracion.html', config=config, system_info=system_info)

# ==================== ADMIN - CACHÉ ====================
@app.route('/admin/cache/limpiar', methods=['GET'])
@login_required
@admin_required
def limpiar_cache():
    try:
        global _config_cache
        _config_cache = None
        flash('Caché limpiada', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(request.referrer or url_for('configuracion'))

# ==================== MANEJADORES DE ERRORES ====================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(e):
    flash('El archivo es demasiado grande. Máximo: 500MB', 'error')
    return redirect(request.url)

# ==================== INICIAR APLICACIÓN ====================
# Variable para PythonAnywhere 
application = app

# ESTO CORRIGE EL ERROR 500 REAL
with app.app_context():
    try:
        from models import db, init_db
        db.create_all()
        init_db()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        # Esto imprimirá el error real en tu Error Log de PythonAnywhere
        print(f"❌ Error crítico al iniciar DB: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)