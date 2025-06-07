"""
Punto de entrada principal para la aplicación FlorezCook en producción.
"""
import os
import logging

# Configurar logging de manera MUY silenciosa para producción
def setup_logging():
    """Configura el logging para el entorno adecuado"""
    if os.getenv('ENV') == 'production' or os.getenv('GAE_ENV') == 'standard':
        # EN PRODUCCIÓN: Solo errores críticos
        logging.basicConfig(
            level=logging.ERROR,
            format='%(levelname)s - %(message)s'
        )
        
        # Evitar propagación duplicada y SILENCIAR todos los loggers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Handler silencioso para producción
        handler = logging.StreamHandler()
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.ERROR)
        
        # Silenciar todos los loggers específicos
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
        logging.getLogger('config.database').setLevel(logging.ERROR)
        logging.getLogger('app').setLevel(logging.ERROR)
        logging.getLogger('main').setLevel(logging.ERROR)
        
    else:
        # Configuración para desarrollo
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

# Configurar logging antes de importar la app
setup_logging()

from app import create_app

# Logger específico para la aplicación
logger = logging.getLogger(__name__)

def get_app_config():
    """Obtiene la configuración de la aplicación."""
    config = {}
    
    is_production = os.getenv('ENV') == 'production' or os.getenv('GAE_ENV') == 'standard'
    
    if is_production:
        # SILENCIOSO - no log en producción
        config.update({
            'DEBUG': False,
            'SECRET_KEY': 'florezcook-production-secret-key-2025-v3-secure-static',
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 1800
        })
        
    else:
        logger.info("Configurando la aplicación para desarrollo")
        config.update({
            'DEBUG': True,
            'SECRET_KEY': 'dev-key-florezcook-2025',
            'SESSION_COOKIE_SECURE': False
        })
        
    return config

# Crear y configurar la aplicación SILENCIOSAMENTE
app = create_app()
app.config.update(get_app_config())

# NO LOG en producción
if os.getenv('ENV') != 'production' and os.getenv('GAE_ENV') != 'standard':
    logger.info("Aplicación configurada para desarrollo")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    if os.getenv('ENV') != 'production':
        logger.info(f"Iniciando aplicación en puerto {port}")
    app.run(host="0.0.0.0", port=port)
