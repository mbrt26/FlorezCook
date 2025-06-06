from sqlalchemy import create_engine, MetaData
from models import Base

# Configurar la conexión a la base de datos
DATABASE_URL = "sqlite:///florez_cook.db"
engine = create_engine(DATABASE_URL)

# Eliminar todas las tablas existentes
print("Eliminando tablas existentes...")
metadata = MetaData()
metadata.reflect(bind=engine)
metadata.drop_all(bind=engine)

# Crear todas las tablas
print("Creando tablas...")
Base.metadata.create_all(engine)

print("¡Base de datos inicializada correctamente!")
print("Tablas creadas:", Base.metadata.tables.keys())
