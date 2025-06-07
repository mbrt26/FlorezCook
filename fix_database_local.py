#!/usr/bin/env python3
"""
Script para actualizar la estructura de la base de datos usando Cloud SQL Proxy local
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

def get_local_proxy_engine():
    """Crea la conexión a Cloud SQL usando el proxy local"""
    try:
        # Configuración para conexión local via proxy
        db_user = "florezcook_user"
        db_pass = "florezcook2025"
        db_name = "florezcook_db"
        
        # Crear la URL de conexión para el proxy local
        database_url = f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:3306/{db_name}'
        
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        logger.info(f"Conectando a Cloud SQL via proxy local en puerto 3306")
        return engine
        
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
                WHERE TABLE_SCHEMA = '{conn.execute(text('SELECT DATABASE()')).fetchone()[0]}'
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
        with engine.begin() as conn:  # Usar begin() para manejar transacciones automáticamente
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
            # No necesitamos commit() aquí porque begin() maneja la transacción automáticamente
            
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
        logger.info("Iniciando actualización de la base de datos via proxy local...")
        
        # Crear conexión a Cloud SQL via proxy
        engine = get_local_proxy_engine()
        
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