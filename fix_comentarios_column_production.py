#!/usr/bin/env python3
"""
Script para migrar la columna observaciones_item a comentarios_item en Cloud SQL (producción)
Este script resuelve el error: Unknown column 'comentarios_item' in 'field list'
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
import pymysql
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cloud_sql_connection():
    """Crea conexión directa a Cloud SQL usando las credenciales de producción"""
    try:
        # Configuración para conexión a Cloud SQL en producción
        db_user = "florezcook_app"
        db_pass = "Catalina18" 
        db_name = "florezcook_db"
        
        # Intentar conexión directa (si está ejecutándose en App Engine)
        db_socket = "/cloudsql/appsindunnova:southamerica-east1:florezcook-instance"
        
        if os.path.exists(db_socket):
            # Conexión desde App Engine usando socket Unix
            database_url = f'mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket={db_socket}'
            logger.info("Conectando a Cloud SQL usando socket Unix (App Engine)")
        else:
            # Conexión usando proxy local (para desarrollo)
            database_url = f'mysql+pymysql://{db_user}:{db_pass}@127.0.0.1:3306/{db_name}'
            logger.info("Conectando a Cloud SQL usando proxy local")
        
        engine = create_engine(
            database_url,
            pool_size=3,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=False
        )
        
        # Probar conexión
        with engine.connect() as conn:
            result = conn.execute(text('SELECT DATABASE() as db_name')).fetchone()
            logger.info(f"✅ Conectado exitosamente a: {result[0]}")
        
        return engine
        
    except Exception as e:
        logger.error(f"Error al conectar a Cloud SQL: {e}")
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
            return result.scalar() > 0
    except Exception as e:
        logger.error(f"Error verificando columna {column_name}: {e}")
        return False

def get_table_structure(engine, table_name):
    """Obtiene la estructura actual de la tabla"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """))
            columns = result.fetchall()
            
            logger.info(f"=== ESTRUCTURA ACTUAL DE {table_name} ===")
            for col in columns:
                logger.info(f"  {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            
            return {col[0]: {'type': col[1], 'nullable': col[2], 'default': col[3]} for col in columns}
    except Exception as e:
        logger.error(f"Error obteniendo estructura de {table_name}: {e}")
        return {}

def migrate_observaciones_to_comentarios(engine):
    """Migra la columna observaciones_item a comentarios_item"""
    try:
        logger.info("=== INICIANDO MIGRACIÓN DE OBSERVACIONES A COMENTARIOS ===")
        
        # Verificar estructura actual
        structure = get_table_structure(engine, 'pedido_productos')
        
        has_observaciones = check_column_exists(engine, 'pedido_productos', 'observaciones_item')
        has_comentarios = check_column_exists(engine, 'pedido_productos', 'comentarios_item')
        
        logger.info(f"observaciones_item existe: {has_observaciones}")
        logger.info(f"comentarios_item existe: {has_comentarios}")
        
        with engine.begin() as conn:
            if has_observaciones and not has_comentarios:
                # Caso 1: Solo existe observaciones_item, necesitamos renombrarla
                logger.info("Renombrando observaciones_item a comentarios_item...")
                conn.execute(text("""
                    ALTER TABLE pedido_productos 
                    CHANGE COLUMN observaciones_item comentarios_item TEXT
                """))
                logger.info("✅ Columna renombrada exitosamente")
                
            elif not has_observaciones and not has_comentarios:
                # Caso 2: Ninguna existe, crear comentarios_item
                logger.info("Creando columna comentarios_item...")
                conn.execute(text("""
                    ALTER TABLE pedido_productos 
                    ADD COLUMN comentarios_item TEXT
                """))
                logger.info("✅ Columna comentarios_item creada exitosamente")
                
            elif has_observaciones and has_comentarios:
                # Caso 3: Ambas existen, migrar datos y eliminar observaciones_item
                logger.info("Migrando datos de observaciones_item a comentarios_item...")
                
                # Migrar datos donde comentarios_item esté vacío
                result = conn.execute(text("""
                    UPDATE pedido_productos 
                    SET comentarios_item = observaciones_item 
                    WHERE observaciones_item IS NOT NULL 
                    AND observaciones_item != ''
                    AND (comentarios_item IS NULL OR comentarios_item = '')
                """))
                
                rows_migrated = result.rowcount
                logger.info(f"✅ Migrados {rows_migrated} registros")
                
                # Verificar que todos los datos importantes fueron migrados
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM pedido_productos 
                    WHERE observaciones_item IS NOT NULL 
                    AND observaciones_item != ''
                    AND (comentarios_item IS NULL OR comentarios_item = '')
                """))
                
                pending_rows = result.scalar()
                
                if pending_rows == 0:
                    logger.info("Eliminando columna observaciones_item obsoleta...")
                    conn.execute(text("ALTER TABLE pedido_productos DROP COLUMN observaciones_item"))
                    logger.info("✅ Columna observaciones_item eliminada")
                else:
                    logger.warning(f"Quedan {pending_rows} registros sin migrar. No se eliminará observaciones_item")
                    
            elif not has_observaciones and has_comentarios:
                # Caso 4: Solo existe comentarios_item, perfecto
                logger.info("✅ La columna comentarios_item ya existe y está lista")
            
            return True
            
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        return False

def fix_other_missing_columns(engine):
    """Corrige otras columnas que pueden estar faltando"""
    try:
        logger.info("=== VERIFICANDO OTRAS COLUMNAS CRÍTICAS ===")
        
        # Verificar y agregar fecha_pedido_item si no existe
        if not check_column_exists(engine, 'pedido_productos', 'fecha_pedido_item'):
            logger.info("Agregando columna fecha_pedido_item...")
            with engine.begin() as conn:
                conn.execute(text("""
                    ALTER TABLE pedido_productos 
                    ADD COLUMN fecha_pedido_item DATE NOT NULL DEFAULT (CURDATE())
                """))
                logger.info("✅ Columna fecha_pedido_item agregada")
        
        # Verificar fecha_creacion y fecha_modificacion
        if not check_column_exists(engine, 'pedido_productos', 'fecha_creacion'):
            logger.info("Agregando columna fecha_creacion...")
            with engine.begin() as conn:
                conn.execute(text("""
                    ALTER TABLE pedido_productos 
                    ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                """))
                logger.info("✅ Columna fecha_creacion agregada")
        
        if not check_column_exists(engine, 'pedido_productos', 'fecha_modificacion'):
            logger.info("Agregando columna fecha_modificacion...")
            with engine.begin() as conn:
                conn.execute(text("""
                    ALTER TABLE pedido_productos 
                    ADD COLUMN fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                """))
                logger.info("✅ Columna fecha_modificacion agregada")
        
        return True
        
    except Exception as e:
        logger.error(f"Error corrigiendo otras columnas: {e}")
        return False

def verify_fix(engine):
    """Verifica que la corrección fue exitosa"""
    try:
        logger.info("=== VERIFICACIÓN FINAL ===")
        
        # Verificar que comentarios_item existe y es funcional
        with engine.connect() as conn:
            # Verificar estructura
            structure = get_table_structure(engine, 'pedido_productos')
            
            # Intentar un INSERT de prueba
            test_data = {
                'pedido_id': 999999,
                'producto_id': 999999,
                'fecha_pedido_item': '2025-06-09',
                'cantidad': 1,
                'gramaje_g_item': 1.0,
                'peso_total_g_item': 1.0,
                'grupo_item': 'test',
                'linea_item': 'test',
                'comentarios_item': 'test comentario',
                'fecha_de_entrega_item': '2025-06-11',
                'estado_del_pedido_item': 'Test'
            }
            
            conn.execute(text("""
                INSERT INTO pedido_productos 
                (pedido_id, producto_id, fecha_pedido_item, cantidad, gramaje_g_item, 
                 peso_total_g_item, grupo_item, linea_item, comentarios_item, 
                 fecha_de_entrega_item, estado_del_pedido_item) 
                VALUES (%(pedido_id)s, %(producto_id)s, %(fecha_pedido_item)s, %(cantidad)s, 
                        %(gramaje_g_item)s, %(peso_total_g_item)s, %(grupo_item)s, %(linea_item)s, 
                        %(comentarios_item)s, %(fecha_de_entrega_item)s, %(estado_del_pedido_item)s)
            """), test_data)
            
            # Eliminar el registro de prueba
            conn.execute(text("DELETE FROM pedido_productos WHERE pedido_id = 999999"))
            conn.commit()
            
            logger.info("✅ El INSERT con comentarios_item funciona correctamente")
            
            # Contar registros totales
            result = conn.execute(text("SELECT COUNT(*) FROM pedido_productos"))
            count = result.scalar()
            logger.info(f"📊 Total de registros en pedido_productos: {count}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error en la verificación: {e}")
        return False

def main():
    """Función principal del script"""
    try:
        logger.info("=== CORRECCIÓN DE COLUMNA COMENTARIOS_ITEM EN PRODUCCIÓN ===")
        
        # Conectar a Cloud SQL
        engine = get_cloud_sql_connection()
        
        # Migrar observaciones_item a comentarios_item
        if not migrate_observaciones_to_comentarios(engine):
            logger.error("❌ Error en la migración de columnas")
            return False
        
        # Corregir otras columnas faltantes
        if not fix_other_missing_columns(engine):
            logger.error("❌ Error corrigiendo otras columnas")
            return False
        
        # Verificar que todo funciona
        if not verify_fix(engine):
            logger.error("❌ Error en la verificación final")
            return False
        
        logger.info("🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        logger.info("La aplicación ahora puede guardar pedidos con comentarios_item")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)