#!/usr/bin/env python3
"""
Script para actualizar la estructura de la base de datos en Cloud SQL
Agrega la columna 'descripcion' faltante en la tabla productos
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
import pymysql

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_cloud_sql_engine():
    """Crea la conexión a Cloud SQL usando las variables de entorno"""
    try:
        db_user = os.environ['DB_USER']
        db_pass = os.environ['DB_PASS']
        db_name = os.environ['DB_NAME']
        connection_name = os.environ['CLOUD_SQL_CONNECTION_NAME']
        
        # Crear la URL de conexión para Cloud SQL
        unix_socket_path = f'/cloudsql/{connection_name}'
        database_url = f'mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket={unix_socket_path}'
        
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        logger.info(f"Conectando a Cloud SQL: {connection_name}")
        return engine
        
    except KeyError as e:
        logger.error(f"Variable de entorno faltante: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al crear la conexión a Cloud SQL: {e}")
        raise

def check_column_exists(engine, table_name, column_name):
    """Verifica si una columna existe en la tabla"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                AND COLUMN_NAME = '{column_name}'
            """))
            count = result.fetchone()[0]
            return count > 0
    except Exception as e:
        logger.error(f"Error al verificar la columna {column_name}: {e}")
        return False

def add_descripcion_column(engine):
    """Agrega la columna descripcion a la tabla productos"""
    try:
        with engine.connect() as conn:
            # Verificar si la columna ya existe
            if check_column_exists(engine, 'productos', 'descripcion'):
                logger.info("La columna 'descripcion' ya existe en la tabla productos")
                return True
            
            # Agregar la columna descripcion
            logger.info("Agregando la columna 'descripcion' a la tabla productos...")
            conn.execute(text("""
                ALTER TABLE productos 
                ADD COLUMN descripcion TEXT AFTER categoria_linea
            """))
            conn.commit()
            
            logger.info("Columna 'descripcion' agregada exitosamente")
            return True
            
    except OperationalError as e:
        if "Duplicate column name" in str(e):
            logger.info("La columna 'descripcion' ya existe")
            return True
        else:
            logger.error(f"Error al agregar la columna descripcion: {e}")
            return False
    except Exception as e:
        logger.error(f"Error inesperado al agregar la columna descripcion: {e}")
        return False

def verify_table_structure(engine):
    """Verifica la estructura de la tabla productos"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                DESCRIBE productos
            """))
            columns = result.fetchall()
            
            logger.info("Estructura actual de la tabla productos:")
            for column in columns:
                logger.info(f"  - {column[0]}: {column[1]}")
            
            return True
    except Exception as e:
        logger.error(f"Error al verificar la estructura de la tabla: {e}")
        return False

def main():
    """Función principal"""
    try:
        logger.info("Iniciando actualización de la base de datos...")
        
        # Verificar variables de entorno
        required_vars = ['DB_USER', 'DB_PASS', 'DB_NAME', 'CLOUD_SQL_CONNECTION_NAME']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {missing_vars}")
            logger.error("Asegúrate de tener configuradas las variables de entorno de Cloud SQL")
            return False
        
        # Crear conexión a Cloud SQL
        engine = get_cloud_sql_engine()
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1')).fetchone()
            if result[0] != 1:
                logger.error("No se pudo verificar la conexión a la base de datos")
                return False
        
        logger.info("Conexión a Cloud SQL verificada correctamente")
        
        # Verificar estructura actual
        logger.info("Verificando estructura actual de la tabla productos...")
        verify_table_structure(engine)
        
        # Agregar la columna descripcion
        if add_descripcion_column(engine):
            logger.info("Actualización completada exitosamente")
            
            # Verificar estructura final
            logger.info("Verificando estructura final...")
            verify_table_structure(engine)
            
            return True
        else:
            logger.error("Error al actualizar la base de datos")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico en la actualización: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)