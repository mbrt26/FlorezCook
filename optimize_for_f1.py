#!/usr/bin/env python3
"""
Script para optimizar FlorezCook para funcionar en instancias F1
Reduce el uso de memoria y mejora el rendimiento
"""

import os
import re

def optimize_app_py():
    """Optimizaciones para app.py"""
    optimizations = """
# Optimizaciones para F1 - Agregar después de crear la app
if os.getenv('INSTANCE_CLASS', 'F2') == 'F1':
    # Reducir workers de Gunicorn
    app.config['GUNICORN_WORKERS'] = 1
    app.config['GUNICORN_THREADS'] = 2
    
    # Reducir tamaño de uploads
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max
    
    # Cache más agresivo
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 604800  # 7 días
    
    # Comprimir respuestas
    from flask_compress import Compress
    Compress(app)
"""
    print("✅ Optimizaciones para app.py generadas")
    return optimizations

def optimize_database_config():
    """Optimizaciones para la configuración de base de datos"""
    optimizations = """
# En config/database.py - Ajustar pool para F1
if os.getenv('INSTANCE_CLASS', 'F2') == 'F1':
    pool_size = 2  # Menos conexiones
    max_overflow = 3
    pool_timeout = 15
    pool_recycle = 900  # 15 minutos
else:
    pool_size = 5
    max_overflow = 10
    pool_timeout = 30
    pool_recycle = 3600
"""
    print("✅ Optimizaciones para database.py generadas")
    return optimizations

def create_cache_config():
    """Crear configuración de cache para reducir queries"""
    cache_config = """
# utils/cache.py - Sistema de cache simple
import functools
import time
from typing import Any, Callable, Optional

class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            # Cache válido por 5 minutos
            if time.time() - self._timestamps[key] < 300:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def clear(self):
        self._cache.clear()
        self._timestamps.clear()

# Cache global
cache = SimpleCache()

def cached(expire_time: int = 300):
    '''Decorador para cachear resultados de funciones'''
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

# Ejemplo de uso:
# @cached(expire_time=600)  # Cache por 10 minutos
# def get_productos_activos():
#     return db.query(Producto).filter(Producto.estado == 'activo').all()
"""
    print("✅ Sistema de cache creado")
    return cache_config

def create_monitoring_script():
    """Script para monitorear el uso de recursos"""
    monitoring = """
# monitor_resources.py - Monitorear uso de recursos en F1
import psutil
import logging
from datetime import datetime

def log_resource_usage():
    '''Log del uso actual de recursos'''
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memoria
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used_mb = memory.used / 1024 / 1024
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Log solo si hay uso alto
    if cpu_percent > 80 or memory_percent > 80:
        logging.warning(
            f"[{timestamp}] Alto uso de recursos - "
            f"CPU: {cpu_percent}%, "
            f"Memoria: {memory_percent}% ({memory_used_mb:.1f}MB)"
        )
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'memory_used_mb': memory_used_mb
    }

# Usar en health check
# @app.route('/health')
# def health():
#     resources = log_resource_usage()
#     return {'status': 'healthy', 'resources': resources}
"""
    print("✅ Script de monitoreo creado")
    return monitoring

def create_startup_optimization():
    """Optimizar el arranque de la aplicación"""
    startup = """
# startup_optimize.py - Optimizaciones de arranque para F1
import os
import sys

def optimize_imports():
    '''Lazy loading de módulos pesados'''
    # Deshabilitar imports no esenciales al inicio
    if os.getenv('INSTANCE_CLASS') == 'F1':
        # Ejemplo: retrasar import de pandas si no es necesario inmediatamente
        sys.modules['pandas'] = None
        
def configure_minimal_logging():
    '''Configurar logging mínimo para F1'''
    import logging
    if os.getenv('INSTANCE_CLASS') == 'F1':
        # Solo errores críticos
        logging.basicConfig(level=logging.ERROR)
        # Deshabilitar logs de librerías
        for logger_name in ['werkzeug', 'sqlalchemy', 'urllib3']:
            logging.getLogger(logger_name).setLevel(logging.ERROR)

def warmup_handler():
    '''Handler para /_ah/warmup requests'''
    # Pre-cargar datos esenciales
    from models import Producto, Cliente
    from config.database import db_config
    
    try:
        db = db_config.get_session()
        # Hacer una query simple para calentar la conexión
        db.query(Producto).first()
        db.close()
        return 'OK', 200
    except:
        return 'Warming up', 200
"""
    print("✅ Optimizaciones de arranque creadas")
    return startup

def main():
    print("\n🚀 Generando optimizaciones para F1...\n")
    
    # Crear directorio docs si no existe
    os.makedirs('docs', exist_ok=True)
    
    # Generar archivo de optimizaciones
    with open('docs/optimizaciones_f1.md', 'w') as f:
        f.write("# Optimizaciones para F1\n\n")
        f.write("## 1. App.py\n```python\n")
        f.write(optimize_app_py())
        f.write("\n```\n\n")
        
        f.write("## 2. Database Config\n```python\n")
        f.write(optimize_database_config())
        f.write("\n```\n\n")
        
        f.write("## 3. Sistema de Cache\n```python\n")
        f.write(create_cache_config())
        f.write("\n```\n\n")
        
        f.write("## 4. Monitoreo de Recursos\n```python\n")
        f.write(create_monitoring_script())
        f.write("\n```\n\n")
        
        f.write("## 5. Optimización de Arranque\n```python\n")
        f.write(create_startup_optimization())
        f.write("\n```\n")
    
    print("\n✅ Archivo de optimizaciones creado en: docs/optimizaciones_f1.md")
    print("\n📝 Próximos pasos:")
    print("1. Aplicar app-f1.yaml: gcloud app deploy app-f1.yaml")
    print("2. Implementar las optimizaciones del código")
    print("3. Monitorear el rendimiento")
    print("4. Considerar migración a PostgreSQL")

if __name__ == "__main__":
    main()