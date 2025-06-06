from models import Base
from sqlalchemy import create_engine

# Configurar la conexión a la base de datos
DATABASE_URL = "sqlite:///florez_cook.db"
engine = create_engine(DATABASE_URL)
from sqlalchemy import inspect

# Crear todas las tablas
Base.metadata.create_all(engine)

print("Base de datos actualizada correctamente.")
print("Tablas existentes:", inspect(engine).get_table_names())
