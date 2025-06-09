#!/usr/bin/env python3
"""
Script para agregar la columna fecha_creacion faltante en la tabla pedido_productos
Este error está impidiendo que se puedan guardar pedidos en la aplicación
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import pymysql

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Crea conexión a Cloud SQL via proxy"""
    try:
        # Configuración para conectar via proxy local
        db_user = "florezcook_user"
        db_pass = "florezcook2025"
        db_name = "florezcook_db"
        
        database_url = f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:3306/{db_name}'
        
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        logger.info("Conectando a Cloud SQL via proxy...")
        return engine
        
    except Exception as e:
        logger.error(f"Error al crear la conexión: {e}")
        raise

def check_pedido_productos_table(engine):
    """Verifica la estructura actual de la tabla pedido_productos"""
    try:
        logger.info("=== VERIFICANDO TABLA PEDIDO_PRODUCTOS ===")
        
        with engine.connect() as conn:
            # Verificar si la tabla existe
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pedido_productos'
            """))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                logger.error("❌ La tabla 'pedido_productos' no existe!")
                return False
            
            # Obtener columnas existentes
            result = conn.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pedido_productos'
                ORDER BY ORDINAL_POSITION
            """))
            columns = result.fetchall()
            
            logger.info("Columnas existentes en pedido_productos:")
            existing_columns = []
            for column in columns:
                logger.info(f"  - {column[0]}: {column[1]} {column[2]} {column[3]}")
                existing_columns.append(column[0])
            
            return existing_columns
            
    except Exception as e:
        logger.error(f"Error verificando tabla pedido_productos: {e}")
        return False

def add_missing_columns_pedido_productos(engine):
    """Agrega las columnas faltantes en la tabla pedido_productos"""
    logger.info("=== AGREGANDO COLUMNAS FALTANTES A PEDIDO_PRODUCTOS ===")
    
    # Columnas que necesita la tabla según el modelo SQLAlchemy y el error reportado
    required_columns = {
        'fecha_pedido_item': 'DATE NOT NULL',  # AGREGADO: Columna que está causando el error
        'fecha_creacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'fecha_modificacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    }
    
    try:
        # Verificar columnas existentes
        existing_columns = check_pedido_productos_table(engine)
        if not existing_columns:
            logger.error("❌ No se pudo obtener la estructura de la tabla")
            return False
        
        with engine.begin() as conn:
            columns_added = 0
            for column_name, column_definition in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE pedido_productos ADD COLUMN {column_name} {column_definition}"
                        logger.info(f"Ejecutando: {sql}")
                        conn.execute(text(sql))
                        logger.info(f"✅ Columna '{column_name}' agregada exitosamente")
                        columns_added += 1
                    except Exception as e:
                        if "Duplicate column name" in str(e):
                            logger.info(f"✅ Columna '{column_name}' ya existe")
                        else:
                            logger.error(f"❌ Error agregando '{column_name}': {e}")
                else:
                    logger.info(f"✅ Columna '{column_name}' ya existe")
            
            if columns_added > 0:
                logger.info(f"🎉 Se agregaron {columns_added} columnas nuevas a la tabla pedido_productos")
            else:
                logger.info("ℹ️  No se necesitaron agregar columnas a la tabla pedido_productos")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Error agregando columnas a pedido_productos: {e}")
        return False

def verify_fix(engine):
    """Verifica que las columnas se agregaron correctamente"""
    logger.info("=== VERIFICACIÓN FINAL ===")
    
    try:
        with engine.connect() as conn:
            # Verificar todas las columnas críticas que estaban faltando
            test_columns = ['fecha_pedido_item', 'fecha_creacion', 'fecha_modificacion']
            
            for column in test_columns:
                try:
                    test_sql = f"SELECT {column} FROM pedido_productos LIMIT 1"
                    result = conn.execute(text(test_sql))
                    logger.info(f"✅ La columna '{column}' está accesible en pedido_productos")
                except Exception as e:
                    logger.error(f"❌ Error verificando columna {column}: {e}")
                    return False
            
            # Intentar el INSERT que estaba fallando originalmente
            try:
                test_insert = """
                    INSERT INTO pedido_productos 
                    (pedido_id, producto_id, fecha_pedido_item, cantidad, gramaje_g_item, 
                     peso_total_g_item, grupo_item, linea_item, comentarios_item, 
                     fecha_de_entrega_item, estado_del_pedido_item, fecha_creacion, fecha_modificacion) 
                    VALUES (999999, 999999, '2025-06-09', 1, 1.0, 1.0, 'test', 'test', 'test', 
                            '2025-06-11', 'Test', NOW(), NOW())
                """
                conn.execute(text(test_insert))
                
                # Eliminar el registro de prueba
                conn.execute(text("DELETE FROM pedido_productos WHERE pedido_id = 999999"))
                conn.commit()
                
                logger.info("✅ El INSERT que estaba fallando ahora funciona correctamente")
                
            except Exception as e:
                logger.error(f"❌ El INSERT de prueba aún falla: {e}")
                return False
            
            # Contar registros
            result = conn.execute(text("SELECT COUNT(*) FROM pedido_productos")).fetchone()
            logger.info(f"📊 Tabla pedido_productos: {result[0]} registros")
            
            return True
                
    except Exception as e:
        logger.error(f"❌ Error en verificación final: {e}")
        return False

def main():
    """Función principal del script"""
    try:
        logger.info("=== INICIANDO REPARACIÓN DE TABLA PEDIDO_PRODUCTOS ===")
        
        # Crear conexión
        engine = get_database_connection()
        
        # Verificar conexión básica
        with engine.connect() as conn:
            result = conn.execute(text('SELECT DATABASE() as db_name')).fetchone()
            logger.info(f"✅ Conectado a la base de datos: {result[0]}")
        
        # Verificar estructura actual
        existing_columns = check_pedido_productos_table(engine)
        if not existing_columns:
            logger.error("❌ No se pudo verificar la tabla pedido_productos")
            return False
        
        # Agregar columnas faltantes
        if not add_missing_columns_pedido_productos(engine):
            logger.error("❌ Error agregando columnas faltantes")
            return False
        
        # Verificación final
        if verify_fix(engine):
            logger.info("🎉 ¡REPARACIÓN COMPLETADA EXITOSAMENTE!")
            logger.info("La tabla pedido_productos ahora tiene todas las columnas necesarias")
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