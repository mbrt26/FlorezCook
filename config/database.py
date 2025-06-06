import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
from dotenv import load_dotenv
import pymysql

# Cargar variables de entorno
load_dotenv()

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Configuración de la base de datos para la aplicación"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _get_database_url(self):
        """Obtiene la URL de conexión a la base de datos según el entorno"""
        
        # Si estamos en producción, usamos la conexión Unix socket
        if os.getenv('ENV') == 'production':
            db_user = os.environ['DB_USER']
            db_pass = os.environ['DB_PASS']
            db_name = os.environ['DB_NAME']
            
            try:
                import google.cloud.sql.connector
                from google.cloud.sql.connector import Connector, IPTypes
                
                connector = Connector()
                
                def getconn():
                    conn = connector.connect(
                        os.environ['CLOUD_SQL_CONNECTION_NAME'],
                        "pymysql",
                        user=db_user,
                        password=db_pass,
                        db=db_name,
                        ip_type=IPTypes.PRIVATE if os.environ.get('PRIVATE_IP') else IPTypes.PUBLIC
                    )
                    return conn
                    
                return create_engine(
                    "mysql+pymysql://",
                    creator=getconn,
                    pool_size=5,
                    max_overflow=2,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True
                )
            except ImportError:
                logger.warning("google-cloud-sql-connector no disponible, usando conexión local")
                # Fallback to local connection
                return create_engine(
                    f"mysql+pymysql://{db_user}:{db_pass}@{os.getenv('DB_HOST', 'localhost')}/{db_name}",
                    pool_size=5,
                    max_overflow=2,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True
                )
        else:
            # Configuración para desarrollo local usando SQLite
            db_path = os.path.join(os.getcwd(), 'florez_cook.db')
            return create_engine(
                f"sqlite:///{db_path}",
                pool_pre_ping=True
            )
    
    def _initialize_database(self):
        """Inicializa la conexión a la base de datos"""
        try:
            self.engine = self._get_database_url()
            
            # Verificar la conexión
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
                logger.info("Conexión a la base de datos establecida correctamente")
            
            # Crear tablas si no existen
            Base.metadata.create_all(bind=self.engine)
            
            # Configurar la sesión de SQLAlchemy
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
            
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            raise
    
    def get_session(self):
        """Obtiene una nueva sesión de base de datos"""
        if not self.SessionLocal:
            raise RuntimeError("Base de datos no inicializada")
        return self.SessionLocal()
    
    def remove_session(self):
        """Remueve las sesiones del scope actual"""
        if self.SessionLocal:
            self.SessionLocal.remove()
    
    def health_check(self):
        """Verifica el estado de la conexión a la base de datos"""
        try:
            db = self.get_session()
            try:
                db.execute(text('SELECT 1'))
                return True, "Database connection healthy"
            finally:
                db.close()
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

# Instancia global de configuración de base de datos
db_config = DatabaseConfig()