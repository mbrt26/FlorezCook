import os
import logging
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging optimizado para producción
def setup_production_logging():
    """Configura logging optimizado para Google Cloud"""
    if os.getenv('ENV') == 'production' or os.getenv('GAE_ENV') == 'standard':
        # Configuración MUY silenciosa para producción
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s - %(message)s')
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
        logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
        logging.getLogger('config.database').setLevel(logging.ERROR)
        logging.getLogger('app').setLevel(logging.ERROR)
        logging.getLogger('main').setLevel(logging.ERROR)
    else:
        # Configuración detallada para desarrollo
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_app():
    """Crea y configura la aplicación Flask"""
    
    # Configurar logging antes de crear la app
    setup_production_logging()
    
    app = Flask(__name__)
    logger = logging.getLogger(__name__)
    
    # Variable para evitar logs duplicados
    is_production = os.getenv('ENV') == 'production' or os.getenv('GAE_ENV') == 'standard'
    
    # Configuración base de la aplicación
    if is_production:
        # SOLO log una vez en producción
        if not hasattr(app, '_florez_config_applied'):
            app.config.update({
                'DEBUG': False,
                'SECRET_KEY': 'florezcook-production-secret-key-2025-v4-stable',
                'SESSION_COOKIE_SECURE': True,
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Lax',
                'PERMANENT_SESSION_LIFETIME': 1800,
                'WTF_CSRF_ENABLED': True,
                'JSON_SORT_KEYS': False
            })
            app._florez_config_applied = True
            
    else:
        logger.info("Configurando aplicación para desarrollo")
        app.config.update({
            'DEBUG': True,
            'SECRET_KEY': 'dev-key-florezcook-2025',
            'SESSION_COOKIE_SECURE': False,
            'WTF_CSRF_ENABLED': False
        })
    
    # Importar y configurar la base de datos SILENCIOSAMENTE
    try:
        from config.database import db_config
        
        # Verificar conectividad básica SOLO si no es producción
        if not is_production:
            health_status, health_message = db_config.health_check()
            if health_status:
                logger.info("✅ Conexión a base de datos verificada")
            else:
                logger.warning(f"⚠️  Base de datos: {health_message}")
        
    except Exception as e:
        if not is_production:
            logger.error(f"❌ Error configurando base de datos: {e}")
        # En producción, continuar sin bloquear la aplicación
    
    # Importar modelos SILENCIOSAMENTE
    try:
        from models import Base, Producto, Cliente, Pedido, PedidoProducto
        # Solo log en desarrollo
        if not is_production:
            logger.info("✅ Modelos importados correctamente")
    except Exception as e:
        if not is_production:
            logger.error(f"❌ Error importando modelos: {e}")
    
    # Registrar blueprints/rutas SILENCIOSAMENTE
    try:
        # Importar rutas
        from routes.health import health_bp
        from routes.productos import productos_bp
        from routes.clientes import clientes_bp, api_clientes_bp
        from routes.pedidos import pedidos_bp
        from routes.reportes import reportes_bp
        from routes.indicadores import indicadores_bp
        
        # Registrar blueprints
        app.register_blueprint(health_bp)
        app.register_blueprint(productos_bp, url_prefix='/productos')
        app.register_blueprint(clientes_bp, url_prefix='/clientes')
        app.register_blueprint(api_clientes_bp)
        app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
        app.register_blueprint(reportes_bp, url_prefix='/reportes')
        app.register_blueprint(indicadores_bp)
        
        # Solo log en desarrollo
        if not is_production:
            logger.info("✅ Rutas registradas correctamente")
        
    except Exception as e:
        if not is_production:
            logger.error(f"❌ Error registrando rutas: {e}")
    
    # Ruta principal
    @app.route('/')
    def home():
        """Página principal de la aplicación"""
        try:
            return '''
            <h1>🍽️ FlorezCook - Sistema de Gestión</h1>
            <p>¡Bienvenido al sistema de gestión de FlorezCook!</p>
            <ul>
                <li><a href="/productos">📦 Gestión de Productos</a></li>
                <li><a href="/importar-productos">📥 Importar Productos</a></li>
                <li><a href="/clientes">👥 Gestión de Clientes</a></li>
                <li><a href="/importar-clientes">📥 Importar Clientes</a></li>
                <li><a href="/pedidos/form">📋 Gestión de Pedidos</a></li>
                <li><a href="/reportes/pedidos">📊 Reportes</a></li>
                <li><a href="/indicadores">📈 Indicadores y KPIs</a></li>
                <li><a href="/healthz">🔍 Estado del Sistema</a></li>
            </ul>
            <footer style="margin-top: 50px; text-align: center; color: #666;">
                <p>&copy; 2025 FlorezCook. Todos los derechos reservados.</p>
            </footer>
            '''
        except Exception as e:
            if not is_production:
                logger.error(f"Error en ruta principal: {e}")
            return f"Error: {e}", 500
    
    # Rutas de acceso directo para importación
    @app.route('/importar-productos')
    def importar_productos():
        """Redirige a la página de importación de productos"""
        from flask import redirect, url_for
        return redirect(url_for('productos.importar'))
    
    @app.route('/importar-clientes')
    def importar_clientes():
        """Redirige a la página de importación de clientes"""
        from flask import redirect, url_for
        return redirect(url_for('clientes.importar'))
    
    # Rutas para archivos estáticos comunes
    @app.route('/favicon.ico')
    def favicon():
        """Maneja el favicon.ico sin generar errores 500"""
        try:
            return app.send_static_file('favicon.ico')
        except Exception:
            # Si no existe el archivo, devolver 204 (No Content) en lugar de 500
            return '', 204
        
    @app.route('/apple-touch-icon.png')
    @app.route('/apple-touch-icon-precomposed.png')
    def apple_touch_icon():
        """Maneja los iconos de Apple sin generar errores 500"""
        try:
            return app.send_static_file('apple-touch-icon.png')
        except Exception:
            # Si no existe el archivo, devolver 204 (No Content) en lugar de 500
            return '', 204
    
    # Manejador de errores global
    @app.errorhandler(500)
    def handle_500(error):
        """Manejador personalizado para errores 500"""
        if not is_production:
            logger.error(f"Error 500: {error}")
        return '''
        <h2>⚠️ Error Interno del Servidor</h2>
        <p>Se ha producido un error interno. Por favor, inténtalo de nuevo más tarde.</p>
        <a href="/">🏠 Volver al inicio</a>
        ''', 500
    
    @app.errorhandler(404)
    def handle_404(error):
        """Manejador personalizado para errores 404"""
        return '''
        <h2>🔍 Página No Encontrada</h2>
        <p>La página que buscas no existe.</p>
        <a href="/">🏠 Volver al inicio</a>
        ''', 404
    
    # Función de limpieza para sesiones de BD
    @app.teardown_appcontext
    def cleanup_db_session(error):
        """Limpia las sesiones de base de datos al final de cada request"""
        try:
            from config.database import db_config
            db_config.remove_session()
        except Exception:
            pass  # Silenciar errores de limpieza en producción
    
    # SOLO log final en desarrollo
    if not is_production:
        logger.info("🎉 Aplicación Flask creada y configurada exitosamente")
    
    return app

# Para desarrollo local
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
