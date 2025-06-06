"""
Punto de entrada principal para la aplicación FlorezCook en producción.
"""
import os
from google.cloud import secretmanager
import google.cloud.logging
from app import app, get_db_engine
from models import Base
import logging

# Configuración de logging para Google Cloud
client = google.cloud.logging.Client()
client.setup_logging()

# Configuración de logging local
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def access_secret_version(secret_id):
    """Accede a un secreto en Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/florezcook/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accediendo al secreto {secret_id}: {e}")
        return None

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    try:
        logger.info("Inicializando la base de datos...")
        engine = get_db_engine()
        
        if engine is not None:
            logger.info("Creando tablas en la base de datos...")
            Base.metadata.create_all(bind=engine)
            logger.info("Base de datos inicializada correctamente")
            return True
        else:
            logger.error("No se pudo obtener el motor de la base de datos")
            return False
            
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise

def create_app():
    """Crea y configura la aplicación Flask."""
    try:
        if os.getenv('FLASK_ENV') == 'production':
            logger.info("Configurando la aplicación para producción")
            app.logger.setLevel(logging.INFO)
            
            # Obtener secretos
            app.config['SECRET_KEY'] = access_secret_version('florezcook-secret-key')
            
            # Asegurarse de que las variables de entorno necesarias estén configuradas
            required_vars = ['CLOUD_SQL_CONNECTION_NAME', 'DB_USER', 'DB_PASS', 'DB_NAME']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.error(f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}")
                raise EnvironmentError(f"Faltan variables de entorno: {', '.join(missing_vars)}")
            
            # Configuración de la base de datos
            with app.app_context():
                if not init_db():
                    logger.error("No se pudo inicializar la base de datos")
                    raise RuntimeError("Fallo en la inicialización de la base de datos")
        else:
            logger.info("Configurando la aplicación para desarrollo")
            app.config['DEBUG'] = True
            with app.app_context():
                init_db()
                
    except Exception as e:
        logger.error(f"Error al configurar la aplicación: {e}")
        raise
        
    return app

# Punto de entrada para Gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
