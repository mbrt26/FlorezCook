#!/usr/bin/env python3
"""
Script definitivo para verificar y arreglar completamente la estructura de la tabla productos en Cloud SQL.
Este script se conecta directamente a la instancia de producción y asegura que todas las columnas existan.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Float, DateTime, Numeric
from sqlalchemy.exc import OperationalError, ProgrammingError
import pymysql
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cloud_sql_connection():
    """Crea conexión directa a Cloud SQL usando las variables de entorno de App Engine"""
    try:
        # Configuración para conexión directa a Cloud SQL en producción
        db_user = "florezcook_user"
        db_pass = "florezcook2025"
        db_name = "florezcook_db"
        db_host = "/cloudsql/appsindunnova:us-central1:florezcook-mysql"
        
        # En App Engine, usar socket Unix para Cloud SQL
        if os.path.exists(db_host):
            database_url = f'mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket={db_host}'
            logger.info("Conectando a Cloud SQL usando socket Unix (App Engine)")
        else:
            # Fallback para desarrollo local con proxy
            database_url = f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:3306/{db_name}'
            logger.info("Conectando a Cloud SQL usando proxy local")
        
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=False  # Cambiar a True para debug SQL
        )
        
        return engine
        
    except Exception as e:
        logger.error(f"Error al crear la conexión a Cloud SQL: {e}")
        raise

def verify_and_create_productos_table(engine):
    """Verifica que la tabla productos exista y tenga todas las columnas necesarias"""
    try:
        with engine.begin() as conn:
            # Verificar si la tabla existe
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'productos'
            """))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                logger.info("La tabla productos no existe. Creándola...")
                # Crear la tabla completa
                conn.execute(text("""
                    CREATE TABLE productos (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        codigo VARCHAR(100) UNIQUE NOT NULL,
                        referencia_de_producto VARCHAR(255) NOT NULL,
                        gramaje_g FLOAT NOT NULL,
                        formulacion_grupo VARCHAR(100),
                        categoria_linea VARCHAR(100),
                        descripcion TEXT,
                        precio_unitario DECIMAL(10,2) DEFAULT 0,
                        unidad_medida VARCHAR(20) DEFAULT 'unidad',
                        estado VARCHAR(20) DEFAULT 'activo',
                        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                        fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """))
                logger.info("Tabla productos creada exitosamente")
                return True
            else:
                logger.info("La tabla productos existe. Verificando columnas...")
                return True
                
    except Exception as e:
        logger.error(f"Error al verificar/crear la tabla productos: {e}")
        return False

def get_existing_columns(engine):
    """Obtiene la lista de columnas existentes en la tabla productos"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'productos'
                ORDER BY ORDINAL_POSITION
            """))
            columns = result.fetchall()
            return {col[0]: {'type': col[1], 'nullable': col[2], 'default': col[3]} for col in columns}
    except Exception as e:
        logger.error(f"Error al obtener columnas existentes: {e}")
        return {}

def ensure_all_columns(engine):
    """Asegura que todas las columnas necesarias existan en la tabla productos"""
    
    # Definir todas las columnas requeridas
    required_columns = {
        'id': {
            'definition': 'INT AUTO_INCREMENT PRIMARY KEY',
            'check_sql': "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'id'"
        },
        'codigo': {
            'definition': 'VARCHAR(100) UNIQUE NOT NULL',
            'alter_sql': "ALTER TABLE productos ADD COLUMN codigo VARCHAR(100) UNIQUE NOT NULL"
        },
        'referencia_de_producto': {
            'definition': 'VARCHAR(255) NOT NULL',
            'alter_sql': "ALTER TABLE productos ADD COLUMN referencia_de_producto VARCHAR(255) NOT NULL"
        },
        'gramaje_g': {
            'definition': 'FLOAT NOT NULL',
            'alter_sql': "ALTER TABLE productos ADD COLUMN gramaje_g FLOAT NOT NULL"
        },
        'formulacion_grupo': {
            'definition': 'VARCHAR(100)',
            'alter_sql': "ALTER TABLE productos ADD COLUMN formulacion_grupo VARCHAR(100)"
        },
        'categoria_linea': {
            'definition': 'VARCHAR(100)',
            'alter_sql': "ALTER TABLE productos ADD COLUMN categoria_linea VARCHAR(100)"
        },
        'descripcion': {
            'definition': 'TEXT',
            'alter_sql': "ALTER TABLE productos ADD COLUMN descripcion TEXT"
        },
        'precio_unitario': {
            'definition': 'DECIMAL(10,2) DEFAULT 0',
            'alter_sql': "ALTER TABLE productos ADD COLUMN precio_unitario DECIMAL(10,2) DEFAULT 0"
        },
        'unidad_medida': {
            'definition': "VARCHAR(20) DEFAULT 'unidad'",
            'alter_sql': "ALTER TABLE productos ADD COLUMN unidad_medida VARCHAR(20) DEFAULT 'unidad'"
        },
        'estado': {
            'definition': "VARCHAR(20) DEFAULT 'activo'",
            'alter_sql': "ALTER TABLE productos ADD COLUMN estado VARCHAR(20) DEFAULT 'activo'"
        },
        'fecha_creacion': {
            'definition': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'alter_sql': "ALTER TABLE productos ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP"
        },
        'fecha_modificacion': {
            'definition': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            'alter_sql': "ALTER TABLE productos ADD COLUMN fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        }
    }
    
    try:
        existing_columns = get_existing_columns(engine)
        logger.info(f"Columnas existentes: {list(existing_columns.keys())}")
        
        with engine.begin() as conn:
            for column_name, column_info in required_columns.items():
                if column_name not in existing_columns:
                    if 'alter_sql' in column_info:
                        logger.info(f"Agregando columna faltante: {column_name}")
                        try:
                            conn.execute(text(column_info['alter_sql']))
                            logger.info(f"✅ Columna '{column_name}' agregada exitosamente")
                        except Exception as e:
                            logger.error(f"❌ Error agregando columna '{column_name}': {e}")
                    else:
                        logger.info(f"Columna '{column_name}' es la clave primaria y debería existir")
                else:
                    logger.info(f"✅ Columna '{column_name}' ya existe")
        
        return True
        
    except Exception as e:
        logger.error(f"Error asegurando columnas: {e}")
        return False

def verify_final_structure(engine):
    """Verifica la estructura final de la tabla productos"""
    try:
        logger.info("=== VERIFICACIÓN FINAL DE LA ESTRUCTURA ===")
        existing_columns = get_existing_columns(engine)
        
        required_columns = [
            'id', 'codigo', 'referencia_de_producto', 'gramaje_g',
            'formulacion_grupo', 'categoria_linea', 'descripcion',
            'precio_unitario', 'unidad_medida', 'estado',
            'fecha_creacion', 'fecha_modificacion'
        ]
        
        logger.info("Estructura final de la tabla productos:")
        for column_name in required_columns:
            if column_name in existing_columns:
                col_info = existing_columns[column_name]
                logger.info(f"  ✅ {column_name}: {col_info['type']}")
            else:
                logger.error(f"  ❌ {column_name}: FALTANTE")
        
        # Verificar con una consulta simple
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM productos"))
            count = result.fetchone()[0]
            logger.info(f"Tabla productos verificada: {count} registros")
        
        return len([col for col in required_columns if col in existing_columns]) == len(required_columns)
        
    except Exception as e:
        logger.error(f"Error en verificación final: {e}")
        return False

def main():
    """Función principal del script"""
    try:
        logger.info("=== INICIANDO VERIFICACIÓN Y REPARACIÓN DE BASE DE DATOS ===")
        
        # Crear conexión a Cloud SQL
        engine = get_cloud_sql_connection()
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text('SELECT DATABASE() as db_name')).fetchone()
            logger.info(f"✅ Conectado exitosamente a la base de datos: {result[0]}")
        
        # Verificar/crear tabla productos
        if not verify_and_create_productos_table(engine):
            logger.error("❌ Error verificando/creando la tabla productos")
            return False
        
        # Asegurar que todas las columnas existan
        if not ensure_all_columns(engine):
            logger.error("❌ Error asegurando todas las columnas")
            return False
        
        # Verificación final
        if verify_final_structure(engine):
            logger.info("🎉 ¡ÉXITO! Todas las columnas están presentes y la tabla está lista")
            return True
        else:
            logger.error("❌ La verificación final falló")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error crítico en la reparación: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)