"""
models.py - Modelos de datos para el Ministerio Jhonatan Danny Rivas
VERSIÓN OPTIMIZADA PARA PYTHONANYWHERE CON SQLITE
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json
import re

# ========================= INICIALIZACIÓN =========================
db = SQLAlchemy()

# ========================= MIXINS =========================

class TimeStampMixin:
    """Añade timestamps created_at y updated_at a los modelos"""
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

class ActivoMixin:
    """Añade campo activo para soft delete"""
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)

# ========================= MODELO USUARIO =========================
class Usuario(UserMixin, TimeStampMixin, ActivoMixin, db.Model):
    """Modelo de usuarios del sistema"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False, nullable=False, index=True)
    es_editor = db.Column(db.Boolean, default=False, nullable=False, index=True)
    nombre_completo = db.Column(db.String(100))
    
    # Avatar (archivo local)
    avatar = db.Column(db.String(500))  # Ruta local
    
    bio = db.Column(db.Text)
    telefono = db.Column(db.String(20))
    color = db.Column(db.String(20), default='#D4AF37')
    ultimo_acceso = db.Column(db.DateTime)
    ultimo_ip = db.Column(db.String(45))

    def set_password(self, password):
        if not password or len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def rol(self):
        if self.es_admin:
            return 'Administrador'
        elif self.es_editor:
            return 'Editor'
        return 'Usuario'

    def tiene_permiso(self, permiso):
        if permiso == 'admin':
            return self.es_admin
        if permiso == 'editor':
            return self.es_editor or self.es_admin
        return False

    @property
    def url_avatar(self):
        """Devuelve la URL del avatar (local)"""
        if self.avatar:
            return f'/static/uploads/images/{self.avatar}'
        return '/static/images/default-avatar.png'

    def __repr__(self):
        return f'<Usuario {self.username}>'


# ========================= MODELOS DE CONTENIDO =========================
class Categoria(TimeStampMixin, ActivoMixin, db.Model):
    """Categorías para videos"""
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(50), default='fas fa-folder')
    color = db.Column(db.String(20), default='#D4AF37')
    orden = db.Column(db.Integer, default=0)
    
    # Relaciones
    videos = db.relationship('Video', back_populates='categoria_rel', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Categoría {self.nombre}>'


class Video(TimeStampMixin, ActivoMixin, db.Model):
    """Modelo para videos completos"""
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    
    # YouTube (opcional)
    youtube_url = db.Column(db.String(500), nullable=True, index=True)
    
    # Archivo local
    archivo = db.Column(db.String(200), nullable=True)
    
    # Thumbnail
    thumbnail = db.Column(db.String(200))  # Archivo local
    thumbnail_auto = db.Column(db.Boolean, default=True)  # Auto de YouTube
    thumbnail_upload = db.Column(db.Boolean, default=False)  # Subido manualmente
    
    duracion = db.Column(db.String(20))
    vistas = db.Column(db.Integer, default=0)
    
    # Relaciones
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id', ondelete='SET NULL'), index=True)
    categoria_rel = db.relationship('Categoria', back_populates='videos')
    
    # Flags
    destacado = db.Column(db.Boolean, default=False, index=True)
    estado = db.Column(db.String(20), default='borrador', index=True)  # publicado, borrador
    fecha_publicacion = db.Column(db.DateTime, default=datetime.now, index=True)

    __table_args__ = (
        db.Index('idx_video_busqueda', 'titulo', 'estado', 'destacado'),
        db.Index('idx_video_categoria_estado', 'categoria_id', 'estado'),
    )

    def incrementar_vistas(self):
        """Incrementa el contador de vistas"""
        self.vistas = (self.vistas or 0) + 1

    @property
    def youtube_id(self):
        """Extrae el ID de YouTube de la URL"""
        if self.youtube_url:
            # Patrones mejorados para YouTube
            patterns = [
                r'(?:v=|/v/|youtu\.be/|shorts/|embed/|watch\?v=)([^&?/\n]+)',
                r'(?:youtube\.com/)([^&?/\n]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, self.youtube_url)
                if match:
                    return match.group(1)
        return None

    @property
    def url_video(self):
        """Devuelve la URL del video (prioridad: YouTube > local)"""
        if self.youtube_url:
            return self.youtube_url
        elif self.archivo:
            return f'/static/uploads/videos/{self.archivo}'
        return None

    @property
    def url_thumbnail(self):
        """Devuelve la URL del thumbnail (prioridad: local > auto)"""
        if self.thumbnail:
            return f'/static/uploads/images/{self.thumbnail}'
        elif self.youtube_id and self.thumbnail_auto:
            return f'https://img.youtube.com/vi/{self.youtube_id}/maxresdefault.jpg'
        return '/static/images/video-placeholder.jpg'

    @property
    def tiempo_lectura(self):
        """Estima el tiempo de lectura basado en la descripción"""
        if self.descripcion:
            palabras = len(self.descripcion.split())
            minutos = max(1, palabras // 200)
            return f'{minutos} min'
        return '1 min'

    def __repr__(self):
        return f'<Video {self.titulo}>'


class Short(TimeStampMixin, ActivoMixin, db.Model):
    """Modelo para shorts (videos cortos verticales)"""
    __tablename__ = 'shorts'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    
    # YouTube (opcional)
    youtube_url = db.Column(db.String(500), nullable=True, index=True)
    
    # Archivo local
    video = db.Column(db.String(200), nullable=True)
    
    # Thumbnail
    thumbnail = db.Column(db.String(200))
    thumbnail_auto = db.Column(db.Boolean, default=True)
    thumbnail_upload = db.Column(db.Boolean, default=False)
    
    duracion = db.Column(db.String(20))
    vistas = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='borrador', index=True)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.now, index=True)

    __table_args__ = (
        db.Index('idx_short_busqueda', 'titulo', 'estado'),
    )

    def incrementar_vistas(self):
        """Incrementa el contador de vistas"""
        self.vistas = (self.vistas or 0) + 1

    @property
    def youtube_id(self):
        """Extrae el ID de YouTube de la URL"""
        if self.youtube_url:
            match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([^&?/]+)', self.youtube_url)
            return match.group(1) if match else None
        return None

    @property
    def url_video(self):
        """Devuelve la URL del video"""
        if self.youtube_url:
            return self.youtube_url
        elif self.video:
            return f'/static/uploads/videos/{self.video}'
        return None

    @property
    def url_thumbnail(self):
        """Devuelve la URL del thumbnail"""
        if self.thumbnail:
            return f'/static/uploads/images/{self.thumbnail}'
        elif self.youtube_id and self.thumbnail_auto:
            return f'https://img.youtube.com/vi/{self.youtube_id}/maxresdefault.jpg'
        return '/static/images/short-placeholder.jpg'

    def __repr__(self):
        return f'<Short {self.titulo}>'


# ========================= MODELOS DE INTERACCIÓN =========================
class Testimonio(TimeStampMixin, db.Model):
    """Testimonios de usuarios"""
    __tablename__ = 'testimonios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120))
    ciudad = db.Column(db.String(100))
    titulo = db.Column(db.String(200))
    texto = db.Column(db.Text, nullable=False)
    publicado = db.Column(db.Boolean, default=False, nullable=False, index=True)
    anonimo = db.Column(db.Boolean, default=False)
    consentimiento = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.now, index=True)

    @property
    def nombre_mostrar(self):
        """Devuelve el nombre a mostrar (anónimo si aplica)"""
        if self.anonimo:
            return 'Anónimo'
        return self.nombre or 'Anónimo'

    def __repr__(self):
        return f'<Testimonio {self.nombre_mostrar}>'


class Oracion(TimeStampMixin, db.Model):
    """Peticiones de oración"""
    __tablename__ = 'oraciones'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), index=True)
    email = db.Column(db.String(120), nullable=False)
    pais = db.Column(db.String(100))
    peticion = db.Column(db.Text, nullable=False)
    urgencia = db.Column(db.String(20), default='normal', nullable=False)
    anonimo = db.Column(db.Boolean, default=False, nullable=False)
    compartir = db.Column(db.Boolean, default=False)
    respondida = db.Column(db.Boolean, default=False, nullable=False, index=True)
    notas_admin = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.now, index=True)

    @property
    def nombre_mostrar(self):
        """Devuelve el nombre a mostrar"""
        if self.anonimo:
            return 'Anónimo'
        return self.nombre or 'Anónimo'

    @property
    def urgencia_icono(self):
        """Devuelve el icono según la urgencia"""
        icons = {
            'normal': '🔵',
            'urgente': '🟠',
            'muy-urgente': '🔴'
        }
        return icons.get(self.urgencia, '🔵')

    def __repr__(self):
        return f'<Oración {self.nombre_mostrar}>'


class Contacto(TimeStampMixin, db.Model):
    """Mensajes de contacto"""
    __tablename__ = 'contactos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    telefono = db.Column(db.String(20))
    asunto = db.Column(db.String(200))
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False, nullable=False, index=True)
    notas_admin = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f'<Contacto {self.nombre}>'


class Invitacion(TimeStampMixin, db.Model):
    """Invitaciones para eventos"""
    __tablename__ = 'invitaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    iglesia = db.Column(db.String(200))
    fecha_evento = db.Column(db.DateTime, index=True)
    hora = db.Column(db.String(20))
    lugar = db.Column(db.String(200), nullable=False)
    tipo_evento = db.Column(db.String(50), nullable=False)
    personas = db.Column(db.Integer)
    expectativas = db.Column(db.Text)
    confirmada = db.Column(db.Boolean, default=False, nullable=False, index=True)
    notas_admin = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime, default=datetime.now, index=True)

    @property
    def tipo_evento_icono(self):
        """Devuelve el icono según el tipo de evento"""
        icons = {
            'culto': '⛪',
            'cruzada': '🌟',
            'retiro': '🏕️',
            'conferencia': '🎯',
            'celula': '🏠',
            'calle': '📢',
            'otro': '📌'
        }
        return icons.get(self.tipo_evento, '📅')

    def __repr__(self):
        return f'<Invitación {self.nombre}>'


class Newsletter(TimeStampMixin, db.Model):
    """Suscriptores al newsletter"""
    __tablename__ = 'newsletter'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    activo = db.Column(db.Boolean, default=True, nullable=False, index=True)
    fecha_suscripcion = db.Column(db.DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f'<Newsletter {self.email}>'


class Galeria(TimeStampMixin, ActivoMixin, db.Model):
    """Galería de imágenes"""
    __tablename__ = 'galeria'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    
    # Archivo local
    archivo = db.Column(db.String(200), nullable=True)
    
    # URL externa
    url_externa = db.Column(db.String(500), nullable=True)
    
    creditos = db.Column(db.String(200))
    es_url = db.Column(db.Boolean, default=False, nullable=False)
    categoria = db.Column(db.String(50), default='eventos', nullable=False, index=True)
    fecha_evento = db.Column(db.DateTime)
    fecha_subida = db.Column(db.DateTime, default=datetime.now, index=True)
    destacada = db.Column(db.Boolean, default=False, nullable=False, index=True)
    orden = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.Index('idx_galeria_categoria_destacada', 'categoria', 'destacada'),
    )

    @property
    def url_imagen(self):
        """Devuelve la URL de la imagen (externa > local)"""
        if self.url_externa:
            return self.url_externa
        elif self.archivo:
            return f'/static/uploads/gallery/{self.archivo}'
        return '/static/images/placeholder.jpg'

    def __repr__(self):
        return f'<Galería {self.titulo}>'


# ========================= MODELOS DE CONFIGURACIÓN =========================
class Configuracion(TimeStampMixin, db.Model):
    """Configuración general del sitio - VERSIÓN SQLITE"""
    __tablename__ = 'configuracion'
    
    id = db.Column(db.Integer, primary_key=True)

    # Configuración general
    sitio_titulo = db.Column(db.String(200), default='Ministerio Jhonatan Danny Rivas', nullable=False)
    sitio_descripcion = db.Column(db.Text)
    sitio_keywords = db.Column(db.String(500))
    sitio_idioma = db.Column(db.String(10), default='es')
    sitio_zona_horaria = db.Column(db.String(50), default='America/Santo_Domingo')
    
    # Logo (archivo local)
    logo = db.Column(db.String(500))  # Archivo local
    
    # Configuración de contenido
    videos_por_pagina = db.Column(db.Integer, default=12)
    shorts_por_pagina = db.Column(db.Integer, default=8)
    comentarios_habilitados = db.Column(db.Boolean, default=True)
    videos_destacados = db.Column(db.Boolean, default=True)
    categorias_orden = db.Column(db.String(20), default='nombre')
    
    # REDES SOCIALES (TUS URLs CORRECTAS)
    facebook_url = db.Column(db.String(500), default='https://www.facebook.com/share/1CbPDerCJ3/')
    instagram_url = db.Column(db.String(500), default='https://www.instagram.com/rivasjonathanoficial')
    youtube_url = db.Column(db.String(500), default='https://youtube.com/@jhonatanrivasoficial4487')
    tiktok_url = db.Column(db.String(500), default='https://www.tiktok.com/@evangelistajhonat8')
    twitter_url = db.Column(db.String(500))
    linkedin_url = db.Column(db.String(500))
    live_tiktok_url = db.Column(db.String(500))
    
    # Contacto
    email_contacto = db.Column(db.String(100), default='info@jhonatandannyrivas.com')
    telefono = db.Column(db.String(20), default='+1 809-915-8969')
    whatsapp = db.Column(db.String(20), default='18099158969')
    direccion = db.Column(db.Text, default='Santo Domingo, República Dominicana')
    latitud = db.Column(db.String(20))
    longitud = db.Column(db.String(20))
    
    # Sistema
    modo_mantenimiento = db.Column(db.Boolean, default=False)
    registro_abierto = db.Column(db.Boolean, default=True)
    youtube_api_key = db.Column(db.String(200))
    recaptcha_key = db.Column(db.String(200))
    backup_frecuencia = db.Column(db.String(20), default='semanal')

    @property
    def url_logo(self):
        """Devuelve la URL del logo (local)"""
        if self.logo:
            return f'/static/uploads/images/{self.logo}'
        return '/static/images/logo-default.png'

    def to_dict(self):
        """Convierte a diccionario para la API/templates"""
        return {
            'sitio_titulo': self.sitio_titulo,
            'sitio_descripcion': self.sitio_descripcion,
            'logo': self.url_logo,
            'facebook_url': self.facebook_url,
            'instagram_url': self.instagram_url,
            'youtube_url': self.youtube_url,
            'tiktok_url': self.tiktok_url,
            'twitter_url': self.twitter_url,
            'linkedin_url': self.linkedin_url,
            'live_tiktok_url': self.live_tiktok_url,
            'email_contacto': self.email_contacto,
            'telefono': self.telefono,
            'whatsapp': self.whatsapp,
            'direccion': self.direccion,
            'videos_por_pagina': self.videos_por_pagina,
            'shorts_por_pagina': self.shorts_por_pagina,
        }

    def __repr__(self):
        return f'<Configuración>'


class Donacion(TimeStampMixin, ActivoMixin, db.Model):
    """Configuración de donaciones"""
    __tablename__ = 'donaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    banco = db.Column(db.String(100))
    titular = db.Column(db.String(200))
    tipo_cuenta = db.Column(db.String(50))
    numero_cuenta = db.Column(db.String(50))
    email_paypal = db.Column(db.String(120))
    paypal_me = db.Column(db.String(100))
    mensaje_bienvenida = db.Column(db.Text)
    mensaje_agradecimiento = db.Column(db.Text)
    versiculo = db.Column(db.String(500))
    versiculo_referencia = db.Column(db.String(100))
    montos_sugeridos = db.Column(db.Text, default='[10,25,50,100,500]')
    
    # Redes sociales para donaciones (opcional)
    facebook = db.Column(db.String(500))
    instagram = db.Column(db.String(500))
    youtube = db.Column(db.String(500))
    whatsapp = db.Column(db.String(20))

    @property
    def montos_lista(self):
        """Devuelve la lista de montos sugeridos"""
        try:
            return json.loads(self.montos_sugeridos) if self.montos_sugeridos else [10, 25, 50, 100, 500]
        except:
            return [10, 25, 50, 100, 500]

    def __repr__(self):
        return f'<Donacion Config>'


# ========================= FUNCIÓN PARA DATOS INICIALES =========================
def crear_datos_iniciales():
    """Crea datos iniciales para la aplicación"""
    from flask import current_app

    # Verificar si ya hay datos
    if Usuario.query.first():
        print("📦 Datos iniciales ya existen")
        return

    print("📦 Creando datos iniciales...")

    try:
        # --- 1. Crear usuario admin ---
        admin = Usuario(
            username='admin',
            email='admin@jhonatandannyrivas.com',
            nombre_completo='Administrador',
            es_admin=True,
            activo=True
        )
        admin.set_password('admin123')  # ¡Cámbiala después!
        db.session.add(admin)

        # --- 2. Crear configuración con TUS REDES SOCIALES ---
        config = Configuracion(
            sitio_titulo='Ministerio Jhonatan Danny Rivas',
            sitio_descripcion='Predicando el evangelio de Jesucristo con poder y autoridad.',
            sitio_keywords='ministerio, cristiano, evangelio, jesus, predicaciones',
            email_contacto='info@jhonatandannyrivas.com',
            telefono='+1 809-915-8969',
            whatsapp='18099158969',
            direccion='Santo Domingo, República Dominicana',
            facebook_url='https://www.facebook.com/share/1CbPDerCJ3/',
            instagram_url='https://www.instagram.com/rivasjonathanoficial',
            youtube_url='https://youtube.com/@jhonatanrivasoficial4487',
            tiktok_url='https://www.tiktok.com/@evangelistajhonat8',
            twitter_url='',
            linkedin_url='',
            live_tiktok_url='https://www.tiktok.com/@evangelistajhonat8/live',
            videos_por_pagina=12,
            shorts_por_pagina=8,
            comentarios_habilitados=True,
            videos_destacados=True
        )
        db.session.add(config)

        # --- 3. Crear configuración de donaciones (opcional) ---
        donacion = Donacion(
            banco='Banco de Reservas',
            titular='Ministerio Jhonatan Danny Rivas',
            tipo_cuenta='Corriente',
            numero_cuenta='123-456-789-0',
            email_paypal='donaciones@ministerio.com',
            paypal_me='MinisterioJDR',
            mensaje_bienvenida='Gracias por tu interés en apoyar este ministerio',
            mensaje_agradecimiento='¡Dios bendiga tu generosidad!',
            versiculo='Cada uno dé como propuso en su corazón; no con tristeza, ni por necesidad, porque Dios ama al dador alegre.',
            versiculo_referencia='2 Corintios 9:7',
            activo=True
        )
        db.session.add(donacion)

        # --- 4. Crear categorías por defecto ---
        categorias = [
            {'nombre': 'Predicaciones', 'slug': 'predicaciones', 'icono': 'fas fa-cross', 'color': '#D4AF37', 'descripcion': 'Predicaciones poderosas de la palabra de Dios'},
            {'nombre': 'Estudios Bíblicos', 'slug': 'estudios-biblicos', 'icono': 'fas fa-bible', 'color': '#2E7D32', 'descripcion': 'Estudios profundos de las escrituras'},
            {'nombre': 'Devocionales', 'slug': 'devocionales', 'icono': 'fas fa-pray', 'color': '#1565C0', 'descripcion': 'Momentos de reflexión y oración'},
            {'nombre': 'Alabanzas', 'slug': 'alabanzas', 'icono': 'fas fa-music', 'color': '#C2185B', 'descripcion': 'Música y alabanza a Dios'},
            {'nombre': 'Testimonios', 'slug': 'testimonios', 'icono': 'fas fa-star', 'color': '#FF8F00', 'descripcion': 'Testimonios de vida transformada'},
        ]
        
        for cat_data in categorias:
            cat_data['orden'] = 0
            categoria = Categoria(**cat_data)
            db.session.add(categoria)

        db.session.commit()
        print("✅ Datos iniciales creados correctamente")
        print("   👤 Admin: admin / admin123")
        print("   📱 WhatsApp: 18099158969")
        print("   📘 Facebook: Configurado")
        print("   📷 Instagram: Configurado")
        print("   🎬 YouTube: Configurado")
        print("   🎵 TikTok: Configurado")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creando datos iniciales: {e}")
        raise e