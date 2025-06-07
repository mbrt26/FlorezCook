#!/usr/bin/env python3
"""
Script para verificar la estructura exacta de la tabla pedido_productos
y identificar por qué está fallando con la columna fecha_pedido_item
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
import pymysql

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """Crea conexión a Cloud SQL via proxy"""
    try:
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

def analyze_pedido_productos_structure(engine):
    """Analiza la estructura completa de la tabla pedido_productos"""
    try:
        logger.info("=== ANÁLISIS COMPLETO DE TABLA PEDIDO_PRODUCTOS ===")
        
        with engine.connect() as conn:
            # 1. Verificar si la tabla existe
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
            
            # 2. Mostrar estructura detallada
            result = conn.execute(text("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pedido_productos'
                ORDER BY ORDINAL_POSITION
            """))
            columns = result.fetchall()
            
            logger.info("Estructura actual de la tabla pedido_productos:")
            logger.info("=" * 80)
            logger.info(f"{'COLUMNA':<25} {'TIPO':<15} {'NULO':<8} {'DEFAULT':<20} {'EXTRA':<15}")
            logger.info("=" * 80)
            
            existing_columns = []
            for column in columns:
                col_name, data_type, is_nullable, default_val, extra = column
                existing_columns.append(col_name)
                default_str = str(default_val) if default_val else "None"
                logger.info(f"{col_name:<25} {data_type:<15} {is_nullable:<8} {default_str:<20} {extra:<15}")
            
            # 3. Verificar si fecha_pedido_item existe
            if 'fecha_pedido_item' in existing_columns:
                logger.warning("⚠️  ENCONTRADA: La columna 'fecha_pedido_item' SÍ existe en la tabla")
                logger.warning("   Pero NO está definida en el modelo SQLAlchemy!")
            else:
                logger.info("ℹ️  La columna 'fecha_pedido_item' NO existe en la tabla")
            
            # 4. Mostrar el CREATE TABLE statement
            try:
                result = conn.execute(text("SHOW CREATE TABLE pedido_productos"))
                create_statement = result.fetchone()[1]
                logger.info("\n=== DEFINICIÓN COMPLETA DE LA TABLA ===")
                logger.info(create_statement)
            except Exception as e:
                logger.warning(f"No se pudo obtener CREATE TABLE: {e}")
            
            # 5. Contar registros
            result = conn.execute(text("SELECT COUNT(*) FROM pedido_productos")).fetchone()
            logger.info(f"\n📊 Registros en la tabla: {result[0]}")
            
            return existing_columns
            
    except Exception as e:
        logger.error(f"Error analizando tabla pedido_productos: {e}")
        return False

def identify_model_vs_db_differences(existing_columns):
    """Identifica diferencias entre el modelo SQLAlchemy y la base de datos"""
    logger.info("\n=== COMPARACIÓN MODELO vs BASE DE DATOS ===")
    
    # Columnas definidas en el modelo SQLAlchemy (según models.py)
    model_columns = [
        'id', 'pedido_id', 'producto_id', 'cantidad', 'gramaje_g_item',
        'peso_total_g_item', 'grupo_item', 'linea_item', 'observaciones_item',
        'fecha_de_entrega_item', 'estado_del_pedido_item', 'fecha_creacion'
    ]
    
    logger.info("Columnas en el modelo SQLAlchemy:")
    for col in model_columns:
        logger.info(f"  📝 {col}")
    
    logger.info("\nComparación:")
    
    # Columnas en BD pero no en modelo
    bd_not_in_model = [col for col in existing_columns if col not in model_columns]
    if bd_not_in_model:
        logger.warning("⚠️  Columnas en BD pero NO en modelo:")
        for col in bd_not_in_model:
            logger.warning(f"  ❌ {col}")
    
    # Columnas en modelo pero no en BD
    model_not_in_bd = [col for col in model_columns if col not in existing_columns]
    if model_not_in_bd:
        logger.error("❌ Columnas en modelo pero NO en BD:")
        for col in model_not_in_bd:
            logger.error(f"  ❌ {col}")
    
    # Columnas que coinciden
    matching_columns = [col for col in model_columns if col in existing_columns]
    logger.info("✅ Columnas que coinciden:")
    for col in matching_columns:
        logger.info(f"  ✅ {col}")
    
    return bd_not_in_model, model_not_in_bd

def suggest_solution(bd_not_in_model, model_not_in_bd):
    """Sugiere la solución para resolver las diferencias"""
    logger.info("\n=== SOLUCIÓN RECOMENDADA ===")
    
    if 'fecha_pedido_item' in bd_not_in_model:
        logger.info("🔧 PROBLEMA IDENTIFICADO:")
        logger.info("   La tabla tiene 'fecha_pedido_item' pero el modelo no")
        logger.info("   MySQL requiere un valor para esta columna al hacer INSERT")
        
        logger.info("\n🛠️  OPCIONES DE SOLUCIÓN:")
        logger.info("   1. AGREGAR al modelo SQLAlchemy la columna 'fecha_pedido_item'")
        logger.info("   2. ELIMINAR de la BD la columna 'fecha_pedido_item'")
        logger.info("   3. HACER que la columna tenga un valor DEFAULT en MySQL")
        
        logger.info("\n✅ RECOMENDACIÓN: Opción 1 - Agregar al modelo")
        logger.info("   Esto mantiene la integridad de los datos existentes")
    
    if model_not_in_bd:
        logger.info("\n🔧 COLUMNAS FALTANTES EN BD:")
        logger.info("   Estas columnas del modelo no existen en la base de datos")
        for col in model_not_in_bd:
            logger.info(f"   - {col}")

def main():
    """Función principal del script"""
    try:
        logger.info("Iniciando análisis de estructura de tabla pedido_productos...")
        
        # Crear conexión
        engine = get_database_connection()
        
        # Verificar conexión básica
        with engine.connect() as conn:
            result = conn.execute(text('SELECT DATABASE() as db_name')).fetchone()
            logger.info(f"✅ Conectado a la base de datos: {result[0]}")
        
        # Analizar estructura
        existing_columns = analyze_pedido_productos_structure(engine)
        if not existing_columns:
            logger.error("❌ No se pudo analizar la estructura")
            return False
        
        # Comparar con modelo
        bd_not_in_model, model_not_in_bd = identify_model_vs_db_differences(existing_columns)
        
        # Sugerir solución
        suggest_solution(bd_not_in_model, model_not_in_bd)
        
        logger.info("\n🎉 Análisis completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error crítico en el análisis: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)