"""
Configuración para Google App Engine.
Este archivo es cargado automáticamente por Google App Engine.
"""
import os
import logging
import json
from google.cloud import secretmanager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret(secret_id, version_id="latest"):
    """
    Obtiene un secreto de Secret Manager.
    
    Args:
        secret_id: ID del secreto a obtener
        version_id: Versión del secreto (por defecto 'latest')
        
    Returns:
        str: Valor del secreto o None si hay un error
    """
    try:
        # Obtener el ID del proyecto de las variables de entorno
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT no está definido")
            return None
            
        # Crear el cliente de Secret Manager
        client = secretmanager.SecretManagerServiceClient()
        
        # Construir el nombre del recurso del secreto
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        
        # Acceder a la versión del secreto
        response = client.access_secret_version(request={"name": name})
        
        # Devolver el valor del secreto
        return response.payload.data.decode("UTF-8")
        
    except Exception as e:
        logger.error(f"Error al obtener el secreto {secret_id}: {e}")
        return None

def get_secrets():
    """
    Obtiene todos los secretos necesarios de Secret Manager.
    """
    secrets = {}
    secret_names = [
        'DB_PASSWORD',
        'SECRET_KEY',
        'DB_USER',
        'DB_NAME',
        'DB_HOST',
        'DB_PORT'
    ]
    
    for secret_name in secret_names:
        secret_value = get_secret(secret_name)
        if secret_value:
            secrets[secret_name] = secret_value
            # Establecer la variable de entorno si no está ya definida
            if secret_name not in os.environ:
                os.environ[secret_name] = secret_value
    
    return secrets

# Cargar secretos al inicio
try:
    secrets = get_secrets()
    logger.info("Secretos cargados exitosamente")
except Exception as e:
    logger.error(f"Error al cargar secretos: {e}")
    secrets = {}

# Configuración de la aplicación
app_config = {
    # Clave secreta para la aplicación (usada para firmar cookies de sesión, etc.)
    'SECRET_KEY': secrets.get('SECRET_KEY', os.environ.get('SECRET_KEY', 'florezcook-secret-key-prod')),
    
    # Configuración de la base de datos
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', ''),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    
    # Configuración de sesión
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    
    # Configuración de CSRF
    'WTF_CSRF_ENABLED': True,
    'WTF_CSRF_SECRET_KEY': os.environ.get('CSRF_SECRET_KEY', 'florezcook-csrf-secret-key'),
    
    # Configuración de subida de archivos
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max-limit
    'UPLOAD_FOLDER': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'),
    'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'gif'},
    
    # Configuración de correo electrónico (opcional)
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
    'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),
    
    # Configuración de la aplicación
    'FLASK_ENV': os.environ.get('FLASK_ENV', 'production'),
    'DEBUG': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
    
    # Configuración de CORS (si es necesario para API)
    'CORS_HEADERS': 'Content-Type',
    
    # Configuración de la base de datos
    'DB_USER': os.environ.get('DB_USER', 'root'),
    'DB_PASS': os.environ.get('DB_PASS', ''),
    'DB_NAME': os.environ.get('DB_NAME', 'florezcook_db'),
    'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
    'ENV': os.environ.get('ENV', 'development'),
    'CLOUD_SQL_CONNECTION_NAME': os.environ.get('CLOUD_SQL_CONNECTION_NAME', '')
}

# Actualizar las variables de entorno
for key, value in app_config.items():
    os.environ[key] = value

# Si estamos en producción, intentamos obtener secretos
if os.environ.get('ENV') == 'production':
    secrets = {
        'DB_PASS': get_secret('DB_PASSWORD'),
        'SECRET_KEY': get_secret('SECRET_KEY')
    }
    
    for key, value in secrets.items():
        if value:
            os.environ[key] = value
