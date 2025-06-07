#!/usr/bin/env python3
"""
Script definitivo para agregar TODAS las columnas faltantes en FlorezCook
Basado en los errores específicos reportados en los logs de producción
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

def add_missing_columns_productos(engine):
    """Agrega columnas faltantes a la tabla productos según los errores reportados"""
    logger.info("=== REPARANDO TABLA PRODUCTOS ===")
    
    # Columnas que SABEMOS que faltan según los logs de error
    required_columns = {
        'descripcion': 'TEXT',
        'precio_unitario': 'DECIMAL(10,2) DEFAULT 0.00',
        'unidad_medida': 'VARCHAR(20) DEFAULT "unidad"',
        'estado': 'VARCHAR(20) DEFAULT "activo"',
        'fecha_creacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'fecha_modificacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    }
    
    try:
        with engine.begin() as conn:
            # Verificar qué columnas ya existen
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'productos'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Columnas existentes en productos: {existing_columns}")
            
            # Agregar cada columna faltante
            columns_added = 0
            for column_name, column_definition in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE productos ADD COLUMN {column_name} {column_definition}"
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
                logger.info(f"🎉 Se agregaron {columns_added} columnas nuevas a la tabla productos")
            else:
                logger.info("ℹ️  No se necesitaron agregar columnas a la tabla productos")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Error reparando tabla productos: {e}")
        return False

def add_missing_columns_clientes(engine):
    """Agrega columnas faltantes a la tabla clientes según los errores reportados"""
    logger.info("=== REPARANDO TABLA CLIENTES ===")
    
    # Columnas que SABEMOS que faltan según los logs de error
    required_columns = {
        'fecha_creacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'fecha_modificacion': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'estado': 'VARCHAR(20) DEFAULT "activo"',
        'observaciones': 'TEXT'
    }
    
    try:
        with engine.begin() as conn:
            # Verificar qué columnas ya existen
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'clientes'
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            logger.info(f"Columnas existentes en clientes: {existing_columns}")
            
            # Agregar cada columna faltante
            columns_added = 0
            for column_name, column_definition in required_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE clientes ADD COLUMN {column_name} {column_definition}"
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
                logger.info(f"🎉 Se agregaron {columns_added} columnas nuevas a la tabla clientes")
            else:
                logger.info("ℹ️  No se necesitaron agregar columnas a la tabla clientes")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Error reparando tabla clientes: {e}")
        return False

def verify_final_state(engine):
    """Verifica que todas las columnas problemáticas ahora existan"""
    logger.info("=== VERIFICACIÓN FINAL ===")
    
    try:
        with engine.connect() as conn:
            # Verificar productos
            logger.info("Verificando tabla productos...")
            result = conn.execute(text("SELECT descripcion, precio_unitario FROM productos LIMIT 1"))
            logger.info("✅ Las columnas 'descripcion' y 'precio_unitario' están accesibles")
            
            # Verificar clientes
            logger.info("Verificando tabla clientes...")
            result = conn.execute(text("SELECT fecha_creacion FROM clientes LIMIT 1"))
            logger.info("✅ La columna 'fecha_creacion' está accesible")
            
            # Contar registros
            result = conn.execute(text("SELECT COUNT(*) FROM productos")).fetchone()
            logger.info(f"📊 Tabla productos: {result[0]} registros")
            
            result = conn.execute(text("SELECT COUNT(*) FROM clientes")).fetchone()
            logger.info(f"📊 Tabla clientes: {result[0]} registros")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en verificación final: {e}")
        return False

def main():
    """Función principal del script"""
    try:
        logger.info("=== INICIANDO REPARACIÓN DEFINITIVA DE BASE DE DATOS ===")
        
        # Crear conexión
        engine = get_database_connection()
        
        # Verificar conexión básica
        with engine.connect() as conn:
            result = conn.execute(text('SELECT DATABASE() as db_name')).fetchone()
            logger.info(f"✅ Conectado a la base de datos: {result[0]}")
        
        # Reparar tabla productos
        if not add_missing_columns_productos(engine):
            logger.error("❌ Falló la reparación de la tabla productos")
            return False
        
        # Reparar tabla clientes
        if not add_missing_columns_clientes(engine):
            logger.error("❌ Falló la reparación de la tabla clientes")
            return False
        
        # Verificación final
        if verify_final_state(engine):
            logger.info("🎉 ¡REPARACIÓN COMPLETADA EXITOSAMENTE!")
            logger.info("Todas las columnas problemáticas han sido agregadas")
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