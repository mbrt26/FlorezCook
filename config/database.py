import os
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
from dotenv import load_dotenv
import pymysql

# Cargar variables de entorno
load_dotenv()

# Configuración del logger - MUY silencioso en producción
if os.getenv('ENV') == 'production' or os.getenv('GAE_ENV') == 'standard':
    # EN PRODUCCIÓN: Solo errores críticos
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    # Silenciar completamente los loggers de SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Variable global para evitar múltiples inicializaciones
_DATABASE_INITIALIZED = False

class DatabaseConfig:
    """Configuración de la base de datos para la aplicación"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        # Solo inicializar si no se ha hecho antes
        global _DATABASE_INITIALIZED
        if not _DATABASE_INITIALIZED:
            self._initialize_database()
            _DATABASE_INITIALIZED = True
        else:
            # Si ya se inicializó, solo configurar el engine y session
            self._setup_existing_connection()
        
    def _setup_existing_connection(self):
        """Configura la conexión usando la configuración existente"""
        try:
            self.engine = self._get_database_url()
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
        except Exception as e:
            if os.getenv('ENV') != 'production':
                logger.error(f"Error configurando conexión existente: {e}")
            raise
        
    def _get_database_url(self):
        """Obtiene la URL de conexión a la base de datos según el entorno"""
        if os.getenv('ENV') == 'production' or os.getenv('GAE_ENV') == 'standard':
            # Configuración para Cloud SQL en App Engine
            db_user = os.getenv('DB_USER')
            db_pass = os.getenv('DB_PASS')
            db_name = os.getenv('DB_NAME')
            connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
            
            # CORREGIDO: Usar /tmp/cloudsql para desarrollo local, /cloudsql para producción
            if os.getenv('GAE_ENV') == 'standard':
                # En App Engine, usar la ubicación estándar
                unix_socket_path = f"/cloudsql/{connection_name}"
            else:
                # En desarrollo local, usar /tmp/cloudsql
                unix_socket_path = f"/tmp/cloudsql/{connection_name}"
            
            # Solo log en desarrollo
            if os.getenv('FLASK_ENV') != 'production':
                logger.info(f"Configurando Cloud SQL con socket: {unix_socket_path}")
            
            try:
                return create_engine(
                    f'mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket={unix_socket_path}',
                    # OPTIMIZACIONES DE RENDIMIENTO:
                    pool_size=10,           # Aumentado de 5 a 10
                    max_overflow=20,        # Aumentado de 2 a 20
                    pool_timeout=60,        # Aumentado de 30 a 60
                    pool_recycle=3600,      # Aumentado de 1800 a 3600 (1 hora)
                    pool_pre_ping=True,
                    # Configuraciones adicionales para mejor rendimiento
                    connect_args={
                        "charset": "utf8mb4",
                        "autocommit": False,
                        "connect_timeout": 60,
                        "read_timeout": 30,
                        "write_timeout": 30
                    },
                    # SILENCIAR LOGS DE SQLALCHEMY EN PRODUCCIÓN
                    echo=False,
                    echo_pool=False
                )
            except Exception as e:
                if os.getenv('ENV') != 'production':
                    logger.error(f"Error al crear engine para Cloud SQL: {e}")
                raise
        else:
            # Configuración para desarrollo local usando SQLite
            db_path = os.path.join(os.getcwd(), 'florez_cook.db')
            if os.getenv('FLASK_ENV') != 'production':
                logger.info(f"Usando SQLite en modo desarrollo: {db_path}")
            return create_engine(
                f"sqlite:///{db_path}",
                pool_pre_ping=True,
                connect_args={"check_same_thread": False},
                echo=False
            )
        
    def _verify_and_fix_productos_table(self):
        """Verifica y repara automáticamente la estructura de la tabla productos"""
        try:
            # SOLO ejecutar en la primera inicialización
            global _DATABASE_INITIALIZED
            if _DATABASE_INITIALIZED:
                return
                
            if os.getenv('ENV') != 'production':
                return  # Solo ejecutar en producción
            
            # Solo log si es necesario
            if os.getenv('FLASK_ENV') != 'production':
                logger.info("Verificando estructura de la tabla productos...")
            
            # Obtener columnas existentes
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'productos'
                """))
                existing_columns = [row[0] for row in result.fetchall()]
            
            # Definir columnas requeridas
            required_columns = {
                'descripcion': "ALTER TABLE productos ADD COLUMN descripcion TEXT",
                'precio_unitario': "ALTER TABLE productos ADD COLUMN precio_unitario DECIMAL(10,2) DEFAULT 0",
                'unidad_medida': "ALTER TABLE productos ADD COLUMN unidad_medida VARCHAR(20) DEFAULT 'unidad'",
                'estado': "ALTER TABLE productos ADD COLUMN estado VARCHAR(20) DEFAULT 'activo'",
                'fecha_creacion': "ALTER TABLE productos ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP",
                'fecha_modificacion': "ALTER TABLE productos ADD COLUMN fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            }
            
            # Agregar columnas faltantes SILENCIOSAMENTE
            missing_columns = []
            with self.engine.begin() as conn:
                for column_name, alter_sql in required_columns.items():
                    if column_name not in existing_columns:
                        try:
                            conn.execute(text(alter_sql))
                            missing_columns.append(column_name)
                        except Exception as e:
                            # SILENCIAR logs duplicados - solo log de errores reales
                            if "Duplicate column name" not in str(e):
                                if os.getenv('FLASK_ENV') != 'production':
                                    logger.error(f"❌ Error agregando columna '{column_name}': {e}")
            
            # Log final SOLO si hubo cambios
            if missing_columns and os.getenv('FLASK_ENV') != 'production':
                logger.info(f"Se agregaron {len(missing_columns)} columnas faltantes: {missing_columns}")
                
        except Exception as e:
            if os.getenv('ENV') != 'production':
                logger.error(f"Error verificando/reparando tabla productos: {e}")
            # No lanzar excepción para no bloquear la aplicación
        
    def _initialize_database(self):
        """Inicializa la conexión a la base de datos"""
        try:
            # SILENCIOSO en producción
            if os.getenv('ENV') != 'production':
                logger.info("Inicializando conexión a la base de datos...")
            self.engine = self._get_database_url()
            
            # Verificar la conexión SILENCIOSAMENTE
            with self.engine.connect() as conn:
                result = conn.execute(text('SELECT 1')).fetchone()
                if result[0] != 1:
                    raise Exception("La verificación de conexión falló")
            
            # Crear tablas de manera segura, verificando antes si existen
            self._create_tables_safely()
            
            # Verificar y reparar estructura de productos automáticamente
            self._verify_and_fix_productos_table()
            
            # Configurar la sesión de SQLAlchemy
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
            
        except Exception as e:
            if os.getenv('ENV') != 'production':
                logger.error(f"Error crítico al inicializar la base de datos: {e}")
            raise
        
    def _create_tables_safely(self):
        """Crea las tablas de manera segura, verificando si ya existen"""
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            # Obtener las tablas que necesitamos crear
            tables_to_create = []
            all_table_names = list(Base.metadata.tables.keys())
            
            for table_name in all_table_names:
                if table_name not in existing_tables:
                    tables_to_create.append(Base.metadata.tables[table_name])
            
            # Crear solo las tablas que no existen SILENCIOSAMENTE
            if tables_to_create:
                Base.metadata.create_all(bind=self.engine, tables=tables_to_create)
                # Solo log en desarrollo
                if os.getenv('ENV') != 'production':
                    logger.info(f"Se crearon {len(tables_to_create)} tablas nuevas")
                
        except Exception as e:
            # Como fallback, intentar el método original pero SILENCIOSO
            try:
                from sqlalchemy.exc import OperationalError
                Base.metadata.create_all(bind=self.engine, checkfirst=True)
            except OperationalError as op_error:
                if "already exists" not in str(op_error):
                    if os.getenv('ENV') != 'production':
                        logger.error(f"Error operacional inesperado: {op_error}")
                    raise
            except Exception as fallback_error:
                # Si ambos métodos fallan, asumir que las tablas ya existen
                pass
        
    def get_session(self):
        """Obtiene una nueva sesión de base de datos"""
        if not self.SessionLocal:
            if os.getenv('ENV') != 'production':
                logger.error("Se intentó obtener una sesión sin inicializar la base de datos")
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
                result = db.execute(text('SELECT 1')).fetchone()
                if result[0] == 1:
                    return True, "Database connection healthy"
                else:
                    return False, "Database verification failed"
            except Exception as e:
                return False, f"Database query failed: {str(e)}"
            finally:
                db.close()
        except Exception as e:
            return False, f"Database session failed: {str(e)}"
    
    def initialize(self):
        """Método público para inicializar/reinicializar la base de datos"""
        try:
            self._initialize_database()
            if os.getenv('ENV') != 'production':
                logger.info("Base de datos inicializada exitosamente")
        except Exception as e:
            if os.getenv('ENV') != 'production':
                logger.error(f"Error al inicializar la base de datos: {e}")
            raise

# Instancia global de configuración de base de datos
db_config = DatabaseConfig()