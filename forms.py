"""
forms.py - Formularios para el Ministerio Jhonatan Danny Rivas
VERSIÓN OPTIMIZADA PARA PYTHONANYWHERE CON SQLITE
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, URLField, DateField, PasswordField, HiddenField, FieldList
from wtforms.validators import DataRequired, Email, Length, Optional, URL, NumberRange, ValidationError, EqualTo, Regexp
import pkg_resources
import re

# Verificar versión de Flask-WTF para compatibilidad
try:
    FLASK_WTF_VERSION = tuple(map(int, pkg_resources.get_distribution('Flask-WTF').version.split('.')))
except:
    FLASK_WTF_VERSION = (1, 0, 0)

# Constantes de tamaño (en bytes)
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_SHORT_SIZE = 200 * 1024 * 1024   # 200MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024    # 10MB

# Extensiones permitidas
ALLOWED_VIDEOS = ['mp4', 'webm', 'mov', 'avi', 'mkv']
ALLOWED_SHORTS = ['mp4', 'webm', 'mov']
ALLOWED_IMAGES = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# Validadores de tamaño según versión
if FLASK_WTF_VERSION >= (1, 1, 0):
    video_size_validator = FileSize(max_size=MAX_VIDEO_SIZE, message='El video no puede ser mayor a 500MB')
    short_size_validator = FileSize(max_size=MAX_SHORT_SIZE, message='El video no puede ser mayor a 200MB')
    image_size_validator = FileSize(max_size=MAX_IMAGE_SIZE, message='La imagen no puede ser mayor a 10MB')
else:
    def video_size_validator(form, field):
        if field.data and hasattr(field.data, 'content_length'):
            if field.data.content_length > MAX_VIDEO_SIZE:
                raise ValidationError('El video no puede ser mayor a 500MB')
    
    def short_size_validator(form, field):
        if field.data and hasattr(field.data, 'content_length'):
            if field.data.content_length > MAX_SHORT_SIZE:
                raise ValidationError('El video no puede ser mayor a 200MB')
    
    def image_size_validator(form, field):
        if field.data and hasattr(field.data, 'content_length'):
            if field.data.content_length > MAX_IMAGE_SIZE:
                raise ValidationError('La imagen no puede ser mayor a 10MB')

# ========================= VALIDADORES PERSONALIZADOS =========================

def validate_slug(form, field):
    """Valida que el slug tenga el formato correcto"""
    if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', field.data):
        raise ValidationError('El slug solo puede contener letras minúsculas, números y guiones')

def validate_youtube_url(form, field):
    """Valida que sea una URL de YouTube válida"""
    if field.data:
        url = field.data.strip()
        
        youtube_patterns = [
            r'^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=([\w-]+)',
            r'^(https?:\/\/)?(www\.)?youtu\.be\/([\w-]+)',
            r'^(https?:\/\/)?(www\.)?youtube\.com\/shorts\/([\w-]+)',
            r'^(https?:\/\/)?(www\.)?youtube\.com\/embed\/([\w-]+)',
            r'^(https?:\/\/)?(www\.)?youtube\.com\/v\/([\w-]+)'
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return
        
        raise ValidationError('❌ Ingresa una URL válida de YouTube (youtube.com, youtu.be, shorts)')

def validate_whatsapp(form, field):
    """Valida número de WhatsApp"""
    if field.data:
        numero = re.sub(r'[^\d]', '', field.data)
        if len(numero) < 10 or len(numero) > 15:
            raise ValidationError('El número debe tener entre 10 y 15 dígitos')

def validate_unique_slug(model, field):
    """Validador factory para slugs únicos"""
    def _validator(form, field):
        from app import db  # Importación diferida para evitar circular imports
        existing = model.query.filter_by(slug=field.data).first()
        if existing and existing.id != form.id.data:
            raise ValidationError('Este slug ya está en uso. Elige otro.')
    return _validator

def validate_unique_url(model, field):
    """Validador factory para URLs únicas"""
    def _validator(form, field):
        if field.data:
            from app import db
            existing = model.query.filter_by(youtube_url=field.data).first()
            if existing and existing.id != form.id.data:
                raise ValidationError('Esta URL de YouTube ya está registrada.')
    return _validator

# ========================= FORMULARIOS ADMIN =========================

class VideoForm(FlaskForm):
    """Formulario para crear/editar videos"""
    id = HiddenField('ID')
    
    titulo = StringField('Título del Video', validators=[
        DataRequired(message='El título es obligatorio'),
        Length(min=3, max=200, message='El título debe tener entre 3 y 200 caracteres')
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=5000, message='La descripción no puede exceder los 5000 caracteres')
    ])
    
    youtube_url = URLField('URL de YouTube', validators=[
        Optional(),
        validate_youtube_url
    ], description='Ej: https://youtube.com/watch?v=... o https://youtu.be/...')
    
    video_file = FileField('Subir archivo de video', validators=[
        Optional(),
        FileAllowed(ALLOWED_VIDEOS, f'Solo se permiten videos: {", ".join(ALLOWED_VIDEOS)}'),
        video_size_validator
    ], description='Alternativa a URL de YouTube (máx 500MB)')
    
    thumbnail_option = SelectField('Tipo de miniatura', choices=[
        ('auto', '🔄 Automática (de YouTube)'),
        ('upload', '📁 Subir imagen')
    ], default='auto', validators=[DataRequired()])
    
    thumbnail = FileField('Subir miniatura', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGES, f'Solo imágenes: {", ".join(ALLOWED_IMAGES)}'),
        image_size_validator
    ], description='Solo si seleccionaste "Subir imagen" (máx 10MB)')
    
    duracion = StringField('Duración', validators=[
        Optional(),
        Length(max=20, message='La duración no puede exceder 20 caracteres'),
        Regexp(r'^(\d+:)?\d{1,2}:\d{2}$', message='Formato inválido. Usa: MM:SS o HH:MM:SS')
    ], description='Ej: 45:30 o 1:15:30')
    
    categoria_id = SelectField('Categoría', coerce=int, validators=[Optional()])
    
    estado = SelectField('Estado', choices=[
        ('publicado', '✅ Publicado (visible)'),
        ('borrador', '📝 Borrador (oculto)')
    ], default='publicado', validators=[DataRequired()])
    
    destacado = BooleanField('⭐ Marcar como video destacado')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validar que al menos una fuente de video esté presente
        if not self.youtube_url.data and not self.video_file.data:
            self.youtube_url.errors.append('Debes proporcionar una URL de YouTube o subir un archivo')
            self.video_file.errors.append('Debes proporcionar una URL de YouTube o subir un archivo')
            return False
        
        return True


class ShortForm(FlaskForm):
    """Formulario para crear/editar shorts"""
    id = HiddenField('ID')
    
    titulo = StringField('Título del Short', validators=[
        DataRequired(message='El título es obligatorio'),
        Length(min=3, max=200, message='El título debe tener entre 3 y 200 caracteres')
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=2000, message='La descripción no puede exceder los 2000 caracteres')
    ])
    
    youtube_url = URLField('URL de YouTube Short', validators=[
        Optional(),
        validate_youtube_url
    ], description='Ej: https://youtube.com/shorts/...')
    
    video_file = FileField('Subir video (formato vertical)', validators=[
        Optional(),
        FileAllowed(ALLOWED_SHORTS, f'Solo se permiten videos: {", ".join(ALLOWED_SHORTS)}'),
        short_size_validator
    ], description='Alternativa a URL de YouTube (máx 200MB, formato 9:16)')
    
    thumbnail_option = SelectField('Tipo de miniatura', choices=[
        ('auto', '🔄 Automática'),
        ('upload', '📁 Subir imagen')
    ], default='auto', validators=[DataRequired()])
    
    thumbnail = FileField('Subir miniatura', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGES, f'Solo imágenes: {", ".join(ALLOWED_IMAGES)}'),
        image_size_validator
    ])
    
    duracion = StringField('Duración', validators=[
        Optional(),
        Length(max=20, message='La duración no puede exceder 20 caracteres'),
        Regexp(r'^\d{1,2}:\d{2}$', message='Formato inválido. Usa: MM:SS')
    ], description='Ej: 0:45')
    
    estado = SelectField('Estado', choices=[
        ('publicado', '✅ Publicado'),
        ('borrador', '📝 Borrador')
    ], default='publicado', validators=[DataRequired()])
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validar que al menos una fuente de video esté presente
        if not self.youtube_url.data and not self.video_file.data:
            self.youtube_url.errors.append('Debes proporcionar una URL de YouTube o subir un archivo')
            self.video_file.errors.append('Debes proporcionar una URL de YouTube o subir un archivo')
            return False
        
        return True


class CategoriaForm(FlaskForm):
    """Formulario para crear/editar categorías"""
    id = HiddenField('ID')
    
    nombre = StringField('Nombre de la categoría', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    slug = StringField('Slug (URL amigable)', validators=[
        DataRequired(message='El slug es obligatorio'),
        Length(min=2, max=100, message='El slug debe tener entre 2 y 100 caracteres'),
        validate_slug
    ], description='Ej: predicaciones, estudios-biblicos (solo minúsculas y guiones)')
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=500, message='La descripción no puede exceder 500 caracteres')
    ])
    
    icono = StringField('Icono FontAwesome', validators=[
        Optional(),
        Length(max=50, message='El icono no puede exceder 50 caracteres')
    ], default='fas fa-folder', description='Ej: fas fa-cross, fas fa-bible')
    
    color = StringField('Color (hexadecimal)', validators=[
        Optional(),
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Debe ser un color hexadecimal válido (#RRGGBB)')
    ], default='#D4AF37', description='Ej: #D4AF37 (dorado)')
    
    orden = IntegerField('Orden de aparición', validators=[
        Optional(),
        NumberRange(min=0, max=999, message='El orden debe estar entre 0 y 999')
    ], default=0, description='Número más bajo = aparece primero')


# ========================= FORMULARIO PARA REDES SOCIALES =========================

class RedesSocialesForm(FlaskForm):
    """Formulario para configuración de redes sociales"""
    
    facebook_url = URLField('Facebook', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL completa de tu página de Facebook')
    
    instagram_url = URLField('Instagram', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL completa de tu perfil de Instagram')
    
    youtube_url = URLField('YouTube', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL de tu canal de YouTube')
    
    tiktok_url = URLField('TikTok', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL de tu perfil de TikTok')
    
    twitter_url = URLField('Twitter / X', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL de tu perfil de Twitter/X')
    
    linkedin_url = URLField('LinkedIn', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL de tu perfil de LinkedIn')
    
    live_tiktok_url = URLField('TikTok (En Vivo)', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='URL específica para transmisiones en vivo (opcional)')


# ========================= FORMULARIOS ADMIN (EDICIÓN) =========================

class TestimonioAdminForm(FlaskForm):
    """Formulario para editar testimonios en admin"""
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])
    
    ciudad = StringField('Ciudad / País', validators=[
        Optional(),
        Length(max=100, message='La ciudad no puede exceder 100 caracteres')
    ])
    
    titulo = StringField('Título', validators=[
        DataRequired(message='El título es obligatorio'),
        Length(min=3, max=200, message='El título debe tener entre 3 y 200 caracteres')
    ])
    
    texto = TextAreaField('Testimonio', validators=[
        DataRequired(message='El testimonio no puede estar vacío'),
        Length(min=10, max=5000, message='El testimonio debe tener entre 10 y 5000 caracteres')
    ])
    
    publicado = BooleanField('✅ Publicado (visible en el sitio)')
    
    anonimo = BooleanField('🙈 Mantener anónimo (no mostrar nombre)')


class OracionAdminForm(FlaskForm):
    """Formulario para administrar peticiones de oración"""
    respondida = BooleanField('✅ Respondida / Atendida')
    
    notas_admin = TextAreaField('Notas internas', validators=[
        Optional(),
        Length(max=1000, message='Las notas no pueden exceder 1000 caracteres')
    ], description='Estas notas solo son visibles para administradores')


class ContactoAdminForm(FlaskForm):
    """Formulario para administrar mensajes de contacto"""
    leido = BooleanField('📖 Marcado como leído')
    
    notas_admin = TextAreaField('Notas internas', validators=[
        Optional(),
        Length(max=1000, message='Las notas no pueden exceder 1000 caracteres')
    ])


class InvitacionAdminForm(FlaskForm):
    """Formulario para administrar invitaciones"""
    confirmada = BooleanField('✅ Confirmada')
    
    notas_admin = TextAreaField('Notas internas', validators=[
        Optional(),
        Length(max=1000, message='Las notas no pueden exceder 1000 caracteres')
    ])


# ========================= FORMULARIOS PÚBLICOS =========================

class TestimonioPublicoForm(FlaskForm):
    """Formulario para que usuarios envíen testimonios"""
    nombre = StringField('Nombre completo', validators=[
        DataRequired(message='Tu nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    email = StringField('Correo electrónico', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])
    
    ciudad = StringField('Ciudad / País', validators=[
        Optional(),
        Length(max=100, message='La ciudad no puede exceder 100 caracteres')
    ])
    
    titulo = StringField('Título del testimonio', validators=[
        DataRequired(message='El título es obligatorio'),
        Length(min=3, max=200, message='El título debe tener entre 3 y 200 caracteres')
    ])
    
    texto = TextAreaField('Tu testimonio', validators=[
        DataRequired(message='El testimonio no puede estar vacío'),
        Length(min=10, max=5000, message='El testimonio debe tener entre 10 y 5000 caracteres')
    ])
    
    consentimiento = BooleanField(
        'Acepto que mi testimonio sea publicado en el sitio web', 
        validators=[DataRequired(message='Debes aceptar para enviar el testimonio')]
    )


class OracionPublicoForm(FlaskForm):
    """Formulario para peticiones de oración"""
    nombre = StringField('Nombre', validators=[
        DataRequired(message='Tu nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])
    
    pais = StringField('País / Ciudad', validators=[
        Optional(),
        Length(max=100, message='El país no puede exceder 100 caracteres')
    ])
    
    peticion = TextAreaField('Petición de oración', validators=[
        DataRequired(message='La petición no puede estar vacía'),
        Length(min=5, max=2000, message='La petición debe tener entre 5 y 2000 caracteres')
    ])
    
    urgencia = SelectField('Nivel de urgencia', choices=[
        ('normal', '🔵 Normal - Oración general'),
        ('urgente', '🟠 Urgente - Necesito oración pronto'),
        ('muy-urgente', '🔴 Muy urgente - Situación crítica')
    ], default='normal', validators=[DataRequired()])
    
    anonimo = BooleanField('Deseo permanecer anónimo (no mostrar mi nombre)')
    
    compartir = BooleanField('Acepto que mi petición sea compartida en oración grupal')


class ContactoPublicoForm(FlaskForm):
    """Formulario de contacto público"""
    nombre = StringField('Nombre completo', validators=[
        DataRequired(message='Tu nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    email = StringField('Correo electrónico', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])
    
    telefono = StringField('Teléfono (opcional)', validators=[
        Optional(),
        Length(max=20, message='El teléfono no puede exceder 20 caracteres')
    ])
    
    asunto = SelectField('Asunto', choices=[
        ('', '-- Selecciona un asunto --'),
        ('oracion', '🙏 Petición de oración'),
        ('invitacion', '🎤 Invitación a predicar'),
        ('consulta', '❓ Consulta general'),
        ('testimonio', '✨ Compartir testimonio'),
        ('donacion', '💰 Información sobre donaciones'),
        ('otro', '📝 Otro')
    ], validators=[DataRequired(message='Selecciona un asunto')])
    
    mensaje = TextAreaField('Mensaje', validators=[
        DataRequired(message='El mensaje no puede estar vacío'),
        Length(min=5, max=5000, message='El mensaje debe tener entre 5 y 5000 caracteres')
    ])


class InvitacionPublicoForm(FlaskForm):
    """Formulario para invitaciones a eventos"""
    nombre = StringField('Nombre completo', validators=[
        DataRequired(message='Tu nombre es obligatorio'),
        Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')
    ])
    
    email = StringField('Correo electrónico', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])
    
    telefono = StringField('Teléfono de contacto', validators=[
        DataRequired(message='El teléfono es obligatorio'),
        Length(min=7, max=20, message='El teléfono debe tener entre 7 y 20 caracteres'),
        Regexp(r'^[\d\s\+\-\(\)]+$', message='Formato de teléfono inválido')
    ])
    
    iglesia = StringField('Iglesia / Ministerio', validators=[
        Optional(),
        Length(max=200, message='El nombre no puede exceder 200 caracteres')
    ])
    
    fecha_evento = DateField('Fecha deseada', format='%Y-%m-%d', validators=[
        DataRequired(message='La fecha es obligatoria')
    ])
    
    hora = SelectField('Horario preferido', choices=[
        ('', '-- Selecciona un horario --'),
        ('manana', '🌅 Mañana (8AM - 12PM)'),
        ('tarde', '☀️ Tarde (2PM - 6PM)'),
        ('noche', '🌙 Noche (7PM - 10PM)'),
        ('madrugada', '⭐ Madrugada (12AM - 6AM)'),
        ('cualquier', '🕒 Cualquier horario')
    ], validators=[DataRequired(message='Selecciona un horario')])
    
    lugar = StringField('Lugar del evento', validators=[
        DataRequired(message='El lugar es obligatorio'),
        Length(min=5, max=200, message='El lugar debe tener entre 5 y 200 caracteres')
    ])
    
    tipo_evento = SelectField('Tipo de evento', choices=[
        ('', '-- Selecciona tipo de evento --'),
        ('culto', '⛪ Culto dominical'),
        ('cruzada', '🌟 Cruzada evangelística'),
        ('retiro', '🏕️ Retiro espiritual'),
        ('conferencia', '🎯 Conferencia'),
        ('celula', '🏠 Célula / Grupo de hogar'),
        ('calle', '📢 Predicación en calle'),
        ('otro', '📌 Otro')
    ], validators=[DataRequired(message='Selecciona el tipo de evento')])
    
    personas = IntegerField('Asistentes aproximados', validators=[
        Optional(),
        NumberRange(min=1, max=10000, message='Ingresa un número entre 1 y 10000')
    ])
    
    expectativas = TextAreaField('Expectativas o tema deseado', validators=[
        Optional(),
        Length(max=2000, message='No puede exceder 2000 caracteres')
    ])


# ========================= FORMULARIOS DE AUTENTICACIÓN =========================

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es obligatorio'),
        Length(min=3, max=50, message='El usuario debe tener entre 3 y 50 caracteres')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=4, max=100, message='La contraseña debe tener entre 4 y 100 caracteres')
    ])
    
    remember = BooleanField('Recordar mi sesión')


class UsuarioForm(FlaskForm):
    """Formulario para crear/editar usuarios"""
    id = HiddenField('ID')
    
    username = StringField('Nombre de usuario', validators=[
        DataRequired(message='El usuario es obligatorio'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Solo letras, números y guión bajo')
    ])
    
    email = StringField('Correo electrónico', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])
    
    password = PasswordField('Contraseña', validators=[
        Optional(),
        Length(min=6, max=100, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    confirm_password = PasswordField('Confirmar contraseña', validators=[
        Optional(),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    
    es_admin = BooleanField('👑 Es administrador (acceso total)')
    
    es_editor = BooleanField('✏️ Es editor (puede crear contenido)')
    
    activo = BooleanField('✅ Activo', default=True)


class CambioPasswordForm(FlaskForm):
    """Formulario para cambiar contraseña"""
    password_actual = PasswordField('Contraseña actual', validators=[
        DataRequired(message='La contraseña actual es obligatoria')
    ])
    
    nueva_password = PasswordField('Nueva contraseña', validators=[
        DataRequired(message='La nueva contraseña es obligatoria'),
        Length(min=6, max=100, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    confirmar_password = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(message='Debes confirmar la contraseña'),
        EqualTo('nueva_password', message='Las contraseñas no coinciden')
    ])


# ========================= FORMULARIOS DE CONFIGURACIÓN =========================

class DonacionConfigForm(FlaskForm):
    """Formulario para configuración de donaciones"""
    banco = StringField('Banco', validators=[
        Optional(),
        Length(max=100, message='No puede exceder 100 caracteres')
    ])
    
    titular = StringField('Titular de la cuenta', validators=[
        Optional(),
        Length(max=200, message='No puede exceder 200 caracteres')
    ])
    
    tipo_cuenta = StringField('Tipo de cuenta', validators=[
        Optional(),
        Length(max=50, message='No puede exceder 50 caracteres')
    ])
    
    numero_cuenta = StringField('Número de cuenta', validators=[
        Optional(),
        Length(max=50, message='No puede exceder 50 caracteres')
    ])
    
    email_paypal = StringField('Email de PayPal', validators=[
        Optional(),
        Email(message='❌ Ingresa un email válido')
    ])
    
    paypal_me = StringField('Usuario de PayPal.me', validators=[
        Optional(),
        Length(max=100, message='No puede exceder 100 caracteres')
    ])
    
    mensaje_bienvenida = TextAreaField('Mensaje de bienvenida', validators=[
        Optional(),
        Length(max=500, message='No puede exceder 500 caracteres')
    ])
    
    mensaje_agradecimiento = TextAreaField('Mensaje de agradecimiento', validators=[
        Optional(),
        Length(max=500, message='No puede exceder 500 caracteres')
    ])
    
    versiculo = StringField('Versículo', validators=[
        Optional(),
        Length(max=200, message='No puede exceder 200 caracteres')
    ])
    
    versiculo_referencia = StringField('Referencia', validators=[
        Optional(),
        Length(max=50, message='No puede exceder 50 caracteres')
    ])
    
    montos_sugeridos_text = StringField('Montos sugeridos (separados por comas)', validators=[
        Optional(),
        Length(max=200, message='No puede exceder 200 caracteres')
    ], description='Ej: 10,25,50,100,500')


class GaleriaForm(FlaskForm):
    """Formulario para subir imágenes a la galería"""
    id = HiddenField('ID')
    
    titulo = StringField('Título', validators=[
        DataRequired(message='El título es obligatorio'),
        Length(min=2, max=200, message='El título debe tener entre 2 y 200 caracteres')
    ])
    
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=500, message='La descripción no puede exceder 500 caracteres')
    ])
    
    categoria = SelectField('Categoría', choices=[
        ('eventos', '📸 Eventos'),
        ('predicaciones', '🎤 Predicaciones'),
        ('campamentos', '🏕️ Campamentos'),
        ('misiones', '🌍 Misiones'),
        ('bautismos', '💧 Bautismos'),
        ('otros', '📁 Otros')
    ], default='eventos', validators=[DataRequired()])
    
    creditos = StringField('Créditos (fotógrafo)', validators=[
        Optional(),
        Length(max=200, message='No puede exceder 200 caracteres')
    ])
    
    fecha_evento = DateField('Fecha del evento', format='%Y-%m-%d', validators=[Optional()])
    
    destacada = BooleanField('⭐ Marcar como destacada')
    
    tipo_imagen = SelectField('Tipo de imagen', choices=[
        ('archivo', '📁 Subir archivo'),
        ('url', '🔗 URL externa')
    ], default='archivo', validators=[DataRequired()])
    
    url_externa = URLField('URL de imagen externa', validators=[
        Optional(),
        URL(require_tld=False, message='❌ Ingresa una URL válida')
    ], description='Solo si seleccionaste "URL externa"')
    
    archivo = FileField('Seleccionar imagen', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGES, f'Solo imágenes: {", ".join(ALLOWED_IMAGES)}'),
        image_size_validator
    ], description='Formatos permitidos: JPG, PNG, GIF, WEBP (máx 10MB)')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        if self.tipo_imagen.data == 'url' and not self.url_externa.data:
            self.url_externa.errors.append('Debes proporcionar una URL')
            return False
        
        if self.tipo_imagen.data == 'archivo' and not self.archivo.data:
            if not self.id.data:  # Solo para creación
                self.archivo.errors.append('Debes seleccionar un archivo')
                return False
        
        return True


class NewsletterForm(FlaskForm):
    """Formulario para suscripción al newsletter"""
    email = StringField('Email', validators=[
        DataRequired(message='El email es obligatorio'),
        Email(message='❌ Ingresa un email válido')
    ])


class ConfiguracionGeneralForm(FlaskForm):
    """Formulario para configuración general del sitio"""
    sitio_titulo = StringField('Título del sitio', validators=[
        Optional(),
        Length(max=200, message='No puede exceder 200 caracteres')
    ])
    
    sitio_descripcion = TextAreaField('Descripción del sitio (Meta description)', validators=[
        Optional(),
        Length(max=500, message='No puede exceder 500 caracteres')
    ])
    
    sitio_keywords = StringField('Palabras clave (SEO)', validators=[
        Optional(),
        Length(max=500, message='No puede exceder 500 caracteres')
    ], description='Separadas por comas')
    
    sitio_idioma = SelectField('Idioma', choices=[
        ('es', 'Español'),
        ('en', 'Inglés'),
        ('pt', 'Portugués')
    ], default='es')
    
    sitio_zona_horaria = SelectField('Zona horaria', choices=[
        ('America/Santo_Domingo', 'Santo Domingo'),
        ('America/New_York', 'Nueva York'),
        ('America/Mexico_City', 'Ciudad de México'),
        ('Europe/Madrid', 'Madrid')
    ], default='America/Santo_Domingo')
    
    logo = FileField('Logo del sitio', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGES, f'Solo imágenes: {", ".join(ALLOWED_IMAGES)}'),
        image_size_validator
    ])
    
    # Email y contacto
    email_contacto = StringField('Email de contacto', validators=[
        Optional(),
        Email(message='❌ Ingresa un email válido')
    ])
    
    telefono = StringField('Teléfono', validators=[
        Optional(),
        Length(max=20)
    ])
    
    whatsapp = StringField('WhatsApp', validators=[
        Optional(),
        Length(max=20),
        validate_whatsapp
    ], description='Solo números, incluyendo código de país (ej: 18099158969)')
    
    direccion = TextAreaField('Dirección', validators=[
        Optional(),
        Length(max=500)
    ])
    
    latitud = StringField('Latitud (para mapas)', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^-?\d{1,3}\.\d+$', message='Formato de latitud inválido')
    ])
    
    longitud = StringField('Longitud (para mapas)', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^-?\d{1,3}\.\d+$', message='Formato de longitud inválido')
    ])
    
    # Configuración de contenido
    videos_por_pagina = IntegerField('Videos por página', validators=[
        Optional(),
        NumberRange(min=1, max=50, message='Debe estar entre 1 y 50')
    ], default=12)
    
    shorts_por_pagina = IntegerField('Shorts por página', validators=[
        Optional(),
        NumberRange(min=1, max=50, message='Debe estar entre 1 y 50')
    ], default=8)
    
    comentarios_habilitados = BooleanField('Habilitar comentarios')
    
    videos_destacados = BooleanField('Mostrar videos destacados')
    
    # Sistema
    modo_mantenimiento = BooleanField('Modo mantenimiento (solo admin puede ver el sitio)')
    
    registro_abierto = BooleanField('Registro de usuarios abierto')
    
    youtube_api_key = StringField('YouTube API Key', validators=[
        Optional(),
        Length(max=200)
    ])
    
    recaptcha_key = StringField('reCAPTCHA Key', validators=[
        Optional(),
        Length(max=200)
    ])


# ========================= VALIDADORES ADICIONALES =========================

def validate_image_extension(form, field):
    """Valida que el archivo tenga extensión de imagen"""
    if field.data:
        ext = field.data.rsplit('.', 1)[1].lower() if '.' in field.data else ''
        if ext not in ALLOWED_IMAGES:
            raise ValidationError(f'Extensión no permitida. Usa: {", ".join(ALLOWED_IMAGES)}')


def validate_video_extension(form, field):
    """Valida que el archivo tenga extensión de video"""
    if field.data:
        ext = field.data.rsplit('.', 1)[1].lower() if '.' in field.data else ''
        if ext not in ALLOWED_VIDEOS:
            raise ValidationError(f'Extensión no permitida. Usa: {", ".join(ALLOWED_VIDEOS)}')