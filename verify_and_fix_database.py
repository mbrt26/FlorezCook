#!/usr/bin/env python3
"""
Script para verificar y corregir la estructura de la base de datos FlorezCook
Conecta a la instancia correcta: florezcook-instance en southamerica-east1
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
import pymysql

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Crea conexión a la instancia correcta de Cloud SQL"""
    try:
        # Configuración para la instancia CORRECTA
        db_user = "florezcook_user"
        db_pass = "florezcook2025"
        db_name = "florezcook_db"
        
        # Conectar via proxy local (puerto 3306)
        database_url = f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:3306/{db_name}'
        
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        logger.info("Conectando a Cloud SQL: florezcook-instance (southamerica-east1)")
        return engine
        
    except Exception as e:
        logger.error(f"Error al crear la conexión: {e}")
        raise

def describe_productos_table(engine):
    """Describe la estructura actual de la tabla productos"""
    try:
        logger.info("=== ESTRUCTURA ACTUAL DE LA TABLA PRODUCTOS ===")
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE productos"))
            columns = result.fetchall()
            
            if not columns:
                logger.error("❌ La tabla 'productos' no existe!")
                return False
            
            logger.info("Columnas existentes:")
            for column in columns:
                logger.info(f"  - {column[0]}: {column[1]} {column[2]} {column[3]} {column[4]} {column[5]}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error al describir la tabla productos: {e}")
        return False

def check_missing_columns(engine):
    """Verifica qué columnas faltan según los errores reportados"""
    try:
        logger.info("=== VERIFICANDO COLUMNAS REQUERIDAS ===")
        
        # Columnas que el modelo SQLAlchemy espera (según los errores)
        required_columns = [
            'id', 'codigo', 'referencia_de_producto', 'gramaje_g',
            'formulacion_grupo', 'categoria_linea', 
            'descripcion',  # Esta está causando errores
            'precio_unitario'  # Esta también está causando errores
        ]
        
        with engine.connect() as conn:
            # Obtener columnas existentes
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'productos'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            logger.info(f"Columnas existentes: {existing_columns}")
            
            missing_columns = []
            for column in required_columns:
                if column not in existing_columns:
                    missing_columns.append(column)
                    logger.error(f"  ❌ FALTA: {column}")
                else:
                    logger.info(f"  ✅ EXISTE: {column}")
            
            if missing_columns:
                logger.warning(f"Se encontraron {len(missing_columns)} columnas faltantes: {missing_columns}")
                return missing_columns
            else:
                logger.info("✅ Todas las columnas requeridas están presentes")
                return []
                
    except Exception as e:
        logger.error(f"Error verificando columnas: {e}")
        return None

def add_missing_columns(engine, missing_columns):
    """Agrega las columnas faltantes a la tabla productos"""
    try:
        if not missing_columns:
            logger.info("No hay columnas que agregar")
            return True
        
        logger.info("=== AGREGANDO COLUMNAS FALTANTES ===")
        
        # Definir las columnas y sus tipos
        column_definitions = {
            'descripcion': 'TEXT',
            'precio_unitario': 'DECIMAL(10,2) DEFAULT 0',
            'unidad_medida': 'VARCHAR(20) DEFAULT "unidad"',
            'estado': 'VARCHAR(20) DEFAULT "activo"',
            'fecha_creacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'fecha_modificacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
        }
        
        with engine.begin() as conn:
            for column in missing_columns:
                if column in column_definitions:
                    definition = column_definitions[column]
                    sql = f"ALTER TABLE productos ADD COLUMN {column} {definition}"
                    
                    try:
                        logger.info(f"Agregando columna: {column}")
                        conn.execute(text(sql))
                        logger.info(f"✅ Columna '{column}' agregada exitosamente")
                    except Exception as e:
                        if "Duplicate column name" in str(e):
                            logger.info(f"✅ Columna '{column}' ya existe")
                        else:
                            logger.error(f"❌ Error agregando '{column}': {e}")
                else:
                    logger.warning(f"⚠️  No se encontró definición para la columna: {column}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error agregando columnas: {e}")
        return False

def verify_connection_to_app(engine):
    """Verifica que la conexión sea la misma que usa la aplicación"""
    try:
        logger.info("=== VERIFICANDO CONECTIVIDAD ===")
        with engine.connect() as conn:
            # Verificar conexión básica
            result = conn.execute(text('SELECT DATABASE() as current_db, CONNECTION_ID() as conn_id')).fetchone()
            logger.info(f"Conectado a base de datos: {result[0]}")
            logger.info(f"ID de conexión: {result[1]}")
            
            # Verificar que podemos hacer una consulta a productos
            try:
                result = conn.execute(text('SELECT COUNT(*) FROM productos')).fetchone()
                logger.info(f"✅ Tabla productos accesible - {result[0]} registros")
                return True
            except Exception as e:
                logger.error(f"❌ Error accediendo a tabla productos: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Error verificando conexión: {e}")
        return False

def main():
    """Función principal"""
    try:
        logger.info("Iniciando verificación y corrección de base de datos FlorezCook...")
        
        # Crear conexión
        engine = get_database_connection()
        
        # Verificar conexión
        if not verify_connection_to_app(engine):
            logger.error("❌ No se pudo establecer conexión válida")
            return False
        
        # Describir estructura actual
        if not describe_productos_table(engine):
            logger.error("❌ No se pudo acceder a la tabla productos")
            return False
        
        # Verificar columnas faltantes
        missing_columns = check_missing_columns(engine)
        if missing_columns is None:
            logger.error("❌ Error verificando columnas")
            return False
        
        # Agregar columnas faltantes
        if missing_columns:
            if not add_missing_columns(engine, missing_columns):
                logger.error("❌ Error agregando columnas faltantes")
                return False
            
            # Verificar nuevamente después de agregar columnas
            logger.info("=== VERIFICACIÓN POST-CORRECCIÓN ===")
            describe_productos_table(engine)
        
        logger.info("🎉 ¡Verificación y corrección completada exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)