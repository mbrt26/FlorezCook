#!/usr/bin/env python3
"""
Script para migrar datos de la columna observaciones_item a comentarios_item
en la tabla pedido_productos para mantener consistencia con el nuevo modelo
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
    """Crea conexión a Cloud SQL usando variables de entorno"""
    try:
        # Verificar variables de entorno requeridas
        required_vars = ['DB_USER', 'DB_PASS', 'DB_NAME', 'CLOUD_SQL_CONNECTION_NAME']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {missing_vars}")
            return None
        
        # Crear string de conexión para Cloud SQL via proxy
        connection_string = (
            f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}"
            f"@localhost:3306/{os.environ['DB_NAME']}"
        )
        
        engine = create_engine(connection_string, echo=False)
        
        # Probar conexión
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        
        logger.info("Conexión a la base de datos establecida correctamente")
        return engine
        
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None

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
        logger.error(f"Error al verificar la columna {column_name}: {e}")
        return False

def migrate_observaciones_to_comentarios(engine):
    """Migra los datos de observaciones_item a comentarios_item"""
    try:
        with engine.begin() as conn:
            # Verificar si ambas columnas existen
            if not check_column_exists(engine, 'pedido_productos', 'observaciones_item'):
                logger.info("La columna 'observaciones_item' no existe, no hay datos que migrar")
                return True
            
            if not check_column_exists(engine, 'pedido_productos', 'comentarios_item'):
                logger.error("La columna 'comentarios_item' no existe, no se puede migrar")
                return False
            
            # Verificar si hay datos para migrar
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pedido_productos 
                WHERE observaciones_item IS NOT NULL 
                AND observaciones_item != ''
                AND (comentarios_item IS NULL OR comentarios_item = '')
            """))
            
            rows_to_migrate = result.scalar()
            
            if rows_to_migrate == 0:
                logger.info("No hay datos para migrar de observaciones_item a comentarios_item")
                return True
            
            logger.info(f"Migrando {rows_to_migrate} registros de observaciones_item a comentarios_item...")
            
            # Migrar los datos
            conn.execute(text("""
                UPDATE pedido_productos 
                SET comentarios_item = observaciones_item 
                WHERE observaciones_item IS NOT NULL 
                AND observaciones_item != ''
                AND (comentarios_item IS NULL OR comentarios_item = '')
            """))
            
            # Verificar la migración
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pedido_productos 
                WHERE comentarios_item IS NOT NULL 
                AND comentarios_item != ''
            """))
            
            migrated_rows = result.scalar()
            
            logger.info(f"Migración completada exitosamente. {migrated_rows} registros con comentarios_item.")
            
            return True
            
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        return False

def cleanup_observaciones_column(engine):
    """Opcional: Elimina la columna observaciones_item después de la migración"""
    try:
        if not check_column_exists(engine, 'pedido_productos', 'observaciones_item'):
            logger.info("La columna 'observaciones_item' ya no existe")
            return True
        
        # Verificar que todos los datos fueron migrados
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pedido_productos 
                WHERE observaciones_item IS NOT NULL 
                AND observaciones_item != ''
                AND (comentarios_item IS NULL OR comentarios_item = '')
            """))
            
            pending_rows = result.scalar()
            
            if pending_rows > 0:
                logger.warning(f"Aún hay {pending_rows} registros sin migrar. No se eliminará la columna observaciones_item")
                return False
        
        # Eliminar la columna observaciones_item
        logger.info("Eliminando la columna 'observaciones_item'...")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE pedido_productos DROP COLUMN observaciones_item"))
        
        logger.info("Columna 'observaciones_item' eliminada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al eliminar la columna observaciones_item: {e}")
        return False

def verify_migration(engine):
    """Verifica que la migración fue exitosa"""
    try:
        with engine.connect() as conn:
            # Verificar que comentarios_item tiene datos
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pedido_productos 
                WHERE comentarios_item IS NOT NULL 
                AND comentarios_item != ''
            """))
            
            comentarios_count = result.scalar()
            
            # Verificar estructura de la tabla
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pedido_productos'
                AND COLUMN_NAME IN ('observaciones_item', 'comentarios_item')
                ORDER BY COLUMN_NAME
            """))
            
            columns = [row[0] for row in result.fetchall()]
            
            logger.info(f"Verificación de migración:")
            logger.info(f"- Registros con comentarios_item: {comentarios_count}")
            logger.info(f"- Columnas existentes: {columns}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error en la verificación: {e}")
        return False

def main():
    """Función principal del script"""
    try:
        logger.info("=== Iniciando migración de observaciones_item a comentarios_item ===")
        
        # Verificar variables de entorno
        required_vars = ['DB_USER', 'DB_PASS', 'DB_NAME', 'CLOUD_SQL_CONNECTION_NAME']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {missing_vars}")
            logger.error("Configura las variables de entorno para Cloud SQL antes de ejecutar")
            return False
        
        # Crear conexión
        engine = get_database_connection()
        if not engine:
            logger.error("No se pudo establecer conexión con la base de datos")
            return False
        
        # Ejecutar migración
        if not migrate_observaciones_to_comentarios(engine):
            logger.error("Error en la migración de datos")
            return False
        
        # Verificar migración
        if not verify_migration(engine):
            logger.error("Error en la verificación de la migración")
            return False
        
        # Opcional: Preguntar si eliminar la columna observaciones_item
        # Por seguridad, no eliminamos automáticamente la columna
        logger.info("")
        logger.info("=== MIGRACIÓN COMPLETADA EXITOSAMENTE ===")
        logger.info("IMPORTANTE: La columna 'observaciones_item' no fue eliminada por seguridad.")
        logger.info("Si estás seguro de que la migración fue exitosa, puedes ejecutar:")
        logger.info("python3 migrate_observaciones_to_comentarios.py --cleanup")
        
        return True
        
    except Exception as e:
        logger.error(f"Error crítico en la migración: {e}")
        return False

if __name__ == "__main__":
    # Verificar si se debe hacer cleanup
    cleanup_mode = '--cleanup' in sys.argv
    
    if cleanup_mode:
        logger.info("=== Modo cleanup: Eliminando columna observaciones_item ===")
        engine = get_database_connection()
        if engine:
            cleanup_observaciones_column(engine)
    else:
        success = main()
        sys.exit(0 if success else 1)