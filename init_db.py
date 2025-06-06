from sqlalchemy import create_engine
from models import Base
import os
from google.cloud import secretmanager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def access_secret(secret_id):
    """Accede a un secreto en Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/florezcook/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accediendo al secreto {secret_id}: {e}")
        return None

def get_db_url():
    """Obtiene la URL de conexión a la base de datos."""
    try:
        db_user = os.environ.get('DB_USER', 'root')
        db_pass = access_secret('florezcook-db-password')
        db_name = os.environ.get('DB_NAME', 'florezcook_db')
        
        if os.getenv('FLASK_ENV') == 'production':
            # Para producción en Cloud SQL
            db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
            cloud_sql_connection_name = access_secret('cloud-sql-connection')
            
            if not cloud_sql_connection_name:
                raise ValueError("No se pudo obtener la conexión a Cloud SQL")
                
            db_url = f"mysql+pymysql://{db_user}:{db_pass}@/{db_name}?" \
                     f"unix_socket={db_socket_dir}/{cloud_sql_connection_name}"
        else:
            # Para desarrollo local
            db_host = os.environ.get('DB_HOST', 'localhost')
            db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
            
        return db_url
        
    except Exception as e:
        logger.error(f"Error configurando la URL de la base de datos: {e}")
        raise

def init_db():
    """Inicializa la base de datos creando todas las tablas."""
    try:
        logger.info("Iniciando la creación de la base de datos...")
        
        # Obtener la URL de conexión
        db_url = get_db_url()
        logger.info(f"URL de conexión configurada")
        
        # Crear el engine con la configuración optimizada
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada exitosamente")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        return False

if __name__ == "__main__":
    init_db()
