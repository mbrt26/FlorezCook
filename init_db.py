import os
from sqlalchemy import create_engine
from models import Base

def init_db():
    # Configuración para producción
    db_user = os.environ.get('DB_USER', 'root')
    db_pass = os.environ.get('DB_PASS', '')
    db_name = os.environ.get('DB_NAME', 'your_database_name')
    db_host = os.environ.get('DB_HOST', 'localhost')
    
    if os.environ.get('ENV') == 'production':
        # Configuración para Cloud SQL
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
                ip_type=IPTypes.PUBLIC
            )
            return conn
            
        engine = create_engine(
            "mysql+pymysql://",
            creator=getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800
        )
    else:
        # Configuración local
        engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}")
    
    # Crear tablas
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(engine)
    print("¡Base de datos inicializada correctamente!")

if __name__ == '__main__':
    init_db()
