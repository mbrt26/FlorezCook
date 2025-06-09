#!/usr/bin/env python3
"""
Script para agregar la columna fecha_pedido_item faltante en la tabla pedido_productos (SQLite)
Este script funciona con la base de datos local SQLite
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sqlite_connection():
    """Crea conexión a la base de datos SQLite local"""
    try:
        db_path = "florez_cook.db"
        if not os.path.exists(db_path):
            logger.error(f"❌ No se encontró la base de datos SQLite: {db_path}")
            return None
        
        conn = sqlite3.connect(db_path)
        logger.info(f"✅ Conectado a SQLite: {db_path}")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Error al conectar a SQLite: {e}")
        return None

def check_table_structure(conn):
    """Verifica la estructura actual de la tabla pedido_productos"""
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='pedido_productos'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.error("❌ La tabla 'pedido_productos' no existe!")
            return False
        
        # Obtener información de las columnas
        cursor.execute("PRAGMA table_info(pedido_productos)")
        columns_info = cursor.fetchall()
        
        logger.info("=== ESTRUCTURA ACTUAL DE PEDIDO_PRODUCTOS ===")
        logger.info(f"{'COLUMNA':<25} {'TIPO':<15} {'NOT NULL':<10} {'DEFAULT':<20}")
        logger.info("=" * 70)
        
        existing_columns = []
        for col in columns_info:
            col_id, name, data_type, not_null, default_val, pk = col
            existing_columns.append(name)
            default_str = str(default_val) if default_val else "None"
            not_null_str = "YES" if not_null else "NO"
            logger.info(f"{name:<25} {data_type:<15} {not_null_str:<10} {default_str:<20}")
        
        return existing_columns
        
    except Exception as e:
        logger.error(f"❌ Error verificando tabla: {e}")
        return False

def add_missing_column(conn):
    """Agrega la columna fecha_pedido_item si no existe"""
    try:
        existing_columns = check_table_structure(conn)
        if not existing_columns:
            return False
        
        if 'fecha_pedido_item' not in existing_columns:
            logger.info("=== AGREGANDO COLUMNA FECHA_PEDIDO_ITEM ===")
            
            cursor = conn.cursor()
            
            # Agregar la columna (SQLite no permite NOT NULL en ALTER TABLE sin default)
            cursor.execute("""
                ALTER TABLE pedido_productos 
                ADD COLUMN fecha_pedido_item DATE
            """)
            
            # Actualizar registros existentes con la fecha de hoy
            today = datetime.now().date().isoformat()
            cursor.execute("""
                UPDATE pedido_productos 
                SET fecha_pedido_item = ? 
                WHERE fecha_pedido_item IS NULL
            """, (today,))
            
            conn.commit()
            
            rows_updated = cursor.rowcount
            logger.info(f"✅ Columna 'fecha_pedido_item' agregada exitosamente")
            logger.info(f"✅ Se actualizaron {rows_updated} registros existentes con fecha {today}")
            
            return True
        else:
            logger.info("✅ La columna 'fecha_pedido_item' ya existe")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error agregando columna: {e}")
        return False

def verify_fix(conn):
    """Verifica que la reparación fue exitosa"""
    try:
        logger.info("=== VERIFICACIÓN FINAL ===")
        cursor = conn.cursor()
        
        # Verificar que la columna existe y es accesible
        cursor.execute("SELECT fecha_pedido_item FROM pedido_productos LIMIT 1")
        logger.info("✅ La columna 'fecha_pedido_item' es accesible")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM pedido_productos")
        count = cursor.fetchone()[0]
        logger.info(f"📊 La tabla tiene {count} registros")
        
        # Intentar un INSERT similar al que estaba fallando
        test_data = {
            'pedido_id': 999999,
            'producto_id': 999999,
            'fecha_pedido_item': '2025-06-09',
            'cantidad': 1,
            'gramaje_g_item': 1.0,
            'peso_total_g_item': 1.0,
            'grupo_item': 'test',
            'linea_item': 'test',
            'comentarios_item': 'test',
            'fecha_de_entrega_item': '2025-06-11',
            'estado_del_pedido_item': 'Test'
        }
        
        cursor.execute("""
            INSERT INTO pedido_productos 
            (pedido_id, producto_id, fecha_pedido_item, cantidad, gramaje_g_item, 
             peso_total_g_item, grupo_item, linea_item, comentarios_item, 
             fecha_de_entrega_item, estado_del_pedido_item) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(test_data.values()))
        
        # Eliminar el registro de prueba
        cursor.execute("DELETE FROM pedido_productos WHERE pedido_id = 999999")
        conn.commit()
        
        logger.info("✅ El INSERT que estaba fallando ahora funciona correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en verificación: {e}")
        return False

def main():
    """Función principal"""
    try:
        logger.info("=== REPARACIÓN DE TABLA PEDIDO_PRODUCTOS (SQLite) ===")
        
        # Conectar a SQLite
        conn = get_sqlite_connection()
        if not conn:
            return False
        
        try:
            # Verificar estructura actual
            if not check_table_structure(conn):
                return False
            
            # Agregar columna faltante
            if not add_missing_column(conn):
                return False
            
            # Verificar que todo funciona
            if not verify_fix(conn):
                return False
            
            logger.info("🎉 ¡REPARACIÓN COMPLETADA EXITOSAMENTE!")
            logger.info("Ahora puedes guardar pedidos sin el error de columna faltante")
            return True
            
        finally:
            conn.close()
            logger.info("Conexión cerrada")
            
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)