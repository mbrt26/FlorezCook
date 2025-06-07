#!/usr/bin/env python3
"""
Script para actualizar completamente la estructura de la tabla productos en Cloud SQL
Agrega todas las columnas faltantes: descripcion, precio_unitario, etc.
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
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                AND COLUMN_NAME = '{column_name}'
            """))
            count = result.fetchone()[0]
            return count > 0
    except Exception as e:
        logger.error(f"Error al verificar la columna {column_name}: {e}")
        return False

def update_productos_table_structure(engine):
    """Actualiza la estructura completa de la tabla productos"""
    try:
        # Lista de columnas que necesitamos agregar
        columns_to_add = [
            {
                'name': 'descripcion',
                'definition': 'TEXT',
                'position': 'AFTER categoria_linea'
            },
            {
                'name': 'precio_unitario',
                'definition': 'DECIMAL(10,2)',
                'position': 'AFTER descripcion'
            },
            {
                'name': 'unidad_medida',
                'definition': 'VARCHAR(20)',
                'position': 'AFTER precio_unitario'
            },
            {
                'name': 'estado',
                'definition': 'VARCHAR(20) DEFAULT "activo"',
                'position': 'AFTER unidad_medida'
            },
            {
                'name': 'fecha_creacion',
                'definition': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                'position': 'AFTER estado'
            },
            {
                'name': 'fecha_modificacion',
                'definition': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
                'position': 'AFTER fecha_creacion'
            }
        ]
        
        with engine.begin() as conn:
            for column in columns_to_add:
                column_name = column['name']
                
                # Verificar si la columna ya existe
                if check_column_exists(engine, 'productos', column_name):
                    logger.info(f"La columna '{column_name}' ya existe en la tabla productos")
                    continue
                
                # Agregar la columna
                logger.info(f"Agregando la columna '{column_name}' a la tabla productos...")
                sql = f"""
                    ALTER TABLE productos 
                    ADD COLUMN {column_name} {column['definition']} {column['position']}
                """
                conn.execute(text(sql))
                logger.info(f"Columna '{column_name}' agregada exitosamente")
            
        return True
            
    except OperationalError as e:
        if "Duplicate column name" in str(e):
            logger.info("Algunas columnas ya existen")
            return True
        else:
            logger.error(f"Error al actualizar la estructura de la tabla: {e}")
            return False
    except Exception as e:
        logger.error(f"Error inesperado al actualizar la estructura de la tabla: {e}")
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
        logger.info("Iniciando actualización completa de la estructura de la tabla productos...")
        
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
        
        # Actualizar la estructura de la tabla
        if update_productos_table_structure(engine):
            logger.info("Actualización de estructura completada exitosamente")
            
            # Verificar estructura final
            logger.info("Verificando estructura final...")
            verify_table_structure(engine)
            
            return True
        else:
            logger.error("Error al actualizar la estructura de la tabla")
            return False
            
    except Exception as e:
        logger.error(f"Error crítico en la actualización: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)