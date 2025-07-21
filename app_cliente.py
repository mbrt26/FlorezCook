#!/usr/bin/env python3
"""
FlorezCook - Aplicativo Cliente
Portal especializado para que los clientes puedan realizar pedidos de forma autónoma.
Solo incluye funcionalidades esenciales para crear y gestionar pedidos.
"""

import os
import logging
from flask import Flask, render_template, redirect, url_for
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def setup_logging():
    """Configura logging para el aplicativo cliente"""
    if os.getenv('ENV') == 'production':
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_cliente_app():
    """Crea y configura la aplicación Flask específica para clientes"""
    
    setup_logging()
    app = Flask(__name__)
    logger = logging.getLogger(__name__)
    
    # Registrar filtros de template personalizados
    from utils.template_filters import register_template_filters
    register_template_filters(app)
    
    # Configuración específica para clientes
    is_production = os.getenv('ENV') == 'production'
    
    if is_production:
        app.config.update({
            'DEBUG': False,
            'SECRET_KEY': 'florezcook-cliente-portal-2025-secure',
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hora para clientes
            'WTF_CSRF_ENABLED': True,
            'JSON_SORT_KEYS': False
        })
    else:
        logger.info("🏗️  Configurando Portal de Clientes para desarrollo")
        app.config.update({
            'DEBUG': True,
            'SECRET_KEY': 'dev-cliente-key-florezcook-2025',
            'SESSION_COOKIE_SECURE': False,
            'WTF_CSRF_ENABLED': False
        })
    
    # Importar y configurar la base de datos
    try:
        from config.database import db_config
        
        if not is_production:
            health_status, health_message = db_config.health_check()
            if health_status:
                logger.info("✅ Conexión a base de datos verificada para Portal de Clientes")
            else:
                logger.warning(f"⚠️  Base de datos: {health_message}")
        
    except Exception as e:
        if not is_production:
            logger.error(f"❌ Error configurando base de datos: {e}")
    
    # Importar modelos necesarios
    try:
        from models import Base, Producto, Cliente, Pedido, PedidoProducto
        if not is_production:
            logger.info("✅ Modelos importados para Portal de Clientes")
    except Exception as e:
        if not is_production:
            logger.error(f"❌ Error importando modelos: {e}")
    
    # Registrar solo las rutas necesarias para clientes
    try:
        # Solo importar las rutas que necesitan los clientes
        from routes.pedidos import pedidos_bp
        from routes.clientes import api_clientes_bp, clientes_bp  # API y gestión básica de clientes
        from routes.productos import productos_bp  # Solo para API de búsqueda de productos
        
        # Registrar blueprints limitados
        app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
        app.register_blueprint(api_clientes_bp)  # API de clientes
        app.register_blueprint(clientes_bp, url_prefix='/clientes')  # Gestión básica de clientes
        
        # Registrar solo la ruta API de productos (no la gestión completa)
        @app.route('/productos/api/buscar')
        def buscar_productos_api():
            """Permite a los clientes buscar productos para sus pedidos"""
            from routes.productos import productos_bp
            from flask import request, jsonify
            from config.database import db_config
            from models import Producto
            
            termino = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 10))
            
            if len(termino) < 1:
                return jsonify([])
            
            db = db_config.get_session()
            try:
                # Buscar productos por código, referencia o línea
                productos = db.query(Producto).filter(
                    (Producto.codigo.ilike(f'%{termino}%')) |
                    (Producto.referencia_de_producto.ilike(f'%{termino}%')) |
                    (Producto.categoria_linea.ilike(f'%{termino}%'))
                ).limit(limit).all()
                
                return jsonify([{
                    'id': p.id,
                    'codigo': p.codigo,
                    'referencia': p.referencia_de_producto,
                    'display': f"{p.codigo} - {p.referencia_de_producto} - {p.categoria_linea or 'Sin línea'}",
                    'gramaje_g': p.gramaje_g,
                    'formulacion_grupo': p.formulacion_grupo or '',
                    'categoria_linea': p.categoria_linea or '',
                    'presentacion1': p.presentacion1 or '',
                    'presentacion2': p.presentacion2 or ''
                } for p in productos])
            finally:
                db.close()
        
        if not is_production:
            logger.info("✅ Rutas de cliente registradas correctamente")
        
    except Exception as e:
        if not is_production:
            logger.error(f"❌ Error registrando rutas de cliente: {e}")
    
    # Middleware para usar templates específicos de clientes
    @app.before_request
    def setup_cliente_context():
        """Configurar contexto específico para portal de clientes"""
        from flask import g, request
        # Marcar que estamos en el portal de clientes
        g.is_cliente_portal = True
        g.template_base = 'base_cliente.html'
        
        # IMPORTANTE: También establecer en el contexto de la aplicación
        app.config['IS_CLIENTE_PORTAL'] = True
        
        # Agregar información adicional para debugging (FORZADO para diagnosticar)
        # TEMPORAL: Siempre loggear para diagnosticar el problema
        logger.warning(f"🎯 CLIENTE PORTAL DEBUG - Ruta: {request.path}, g.is_cliente_portal: {g.is_cliente_portal}, ENV: {os.getenv('ENV')}")
    
    # Ruta alternativa para compatibilidad con URLs existentes
    @app.route('/cliente/nuevo', methods=['GET', 'POST'])
    def nuevo_cliente():
        """Redirigir a la ruta correcta del blueprint de clientes"""
        from flask import request
        # Preservar todos los parámetros de la URL
        query_string = request.query_string.decode('utf-8')
        if query_string:
            return redirect(f'/clientes/agregar?{query_string}')
        else:
            return redirect('/clientes/agregar')
    
    # Página principal del portal de clientes
    @app.route('/')
    def portal_cliente():
        """Página principal del portal de clientes"""
        try:
            return render_template('base_cliente.html')
        except Exception as e:
            # Si no existe el template, mostrar página simple
            return '''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>FlorezCook - Portal de Clientes</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                <style>
                    :root {
                        --florez-primary: #e85a0c;
                        --florez-secondary: #f8f9fa;
                    }
                    .navbar-brand img {
                        height: 40px;
                    }
                    .hero-section {
                        background: linear-gradient(135deg, var(--florez-primary), #d04c06);
                        color: white;
                        padding: 4rem 0;
                    }
                    .btn-florez {
                        background-color: var(--florez-primary);
                        border-color: var(--florez-primary);
                        color: white;
                    }
                    .btn-florez:hover {
                        background-color: #d04c06;
                        border-color: #d04c06;
                        color: white;
                    }
                </style>
            </head>
            <body>
                <nav class="navbar navbar-expand-lg navbar-dark" style="background-color: var(--florez-primary);">
                    <div class="container">
                        <a class="navbar-brand" href="/">
                            <img src="/static/logo1.png" alt="FlorezCook" class="me-2">
                            FlorezCook Portal de Clientes
                        </a>
                    </div>
                </nav>
                
                <div class="hero-section text-center">
                    <div class="container">
                        <h1 class="display-4 mb-4">
                            <i class="fas fa-utensils me-3"></i>
                            Bienvenido al Portal de Clientes FlorezCook
                        </h1>
                        <p class="lead mb-4">Realiza tus pedidos de forma rápida y sencilla</p>
                        <a href="/pedidos/form" class="btn btn-light btn-lg">
                            <i class="fas fa-clipboard-list me-2"></i>
                            Hacer un Pedido
                        </a>
                    </div>
                </div>
                
                <div class="container my-5">
                    <div class="row">
                        <div class="col-md-4 mb-4">
                            <div class="card h-100 text-center">
                                <div class="card-body">
                                    <i class="fas fa-shopping-cart fa-3x text-primary mb-3"></i>
                                    <h5 class="card-title">Pedidos Rápidos</h5>
                                    <p class="card-text">Realiza tus pedidos de manera eficiente con nuestro sistema intuitivo.</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="card h-100 text-center">
                                <div class="card-body">
                                    <i class="fas fa-search fa-3x text-success mb-3"></i>
                                    <h5 class="card-title">Búsqueda Inteligente</h5>
                                    <p class="card-text">Encuentra productos fácilmente por código o descripción.</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="card h-100 text-center">
                                <div class="card-body">
                                    <i class="fas fa-mobile-alt fa-3x text-warning mb-3"></i>
                                    <h5 class="card-title">Optimizado para Móvil</h5>
                                    <p class="card-text">Accede desde cualquier dispositivo con una experiencia optimizada.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center mt-5">
                        <h3 class="mb-4">¿Listo para hacer tu pedido?</h3>
                        <a href="/pedidos/form" class="btn btn-florez btn-lg">
                            <i class="fas fa-play me-2"></i>
                            Comenzar Ahora
                        </a>
                    </div>
                </div>
                
                <footer class="bg-light py-4 mt-5">
                    <div class="container text-center">
                        <p class="mb-0">&copy; 2025 FlorezCook. Portal de Clientes - Todos los derechos reservados.</p>
                    </div>
                </footer>
                
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            '''
    
    # Redirigir directamente al formulario de pedidos
    @app.route('/nuevo-pedido')
    @app.route('/pedido')
    def nuevo_pedido():
        """Redirige al formulario de pedidos"""
        return redirect(url_for('pedidos.form'))
    
    # Manejo de errores específico para clientes
    @app.errorhandler(404)
    def not_found_cliente(error):
        """Error 404 personalizado para clientes"""
        try:
            return render_template('404_cliente.html'), 404
        except:
            return '''
            <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                <h1 style="color: #e85a0c;"><i class="fas fa-search"></i> Página no encontrada</h1>
                <p>La página que buscas no está disponible en el portal de clientes.</p>
                <a href="/" style="color: #e85a0c; text-decoration: none;">
                    <i class="fas fa-home"></i> Volver al inicio
                </a>
            </div>
            ''', 404
    
    @app.errorhandler(500)
    def error_interno_cliente(error):
        """Error 500 personalizado para clientes"""
        try:
            return render_template('500_cliente.html'), 500
        except:
            return '''
            <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                <h1 style="color: #dc3545;"><i class="fas fa-exclamation-triangle"></i> Error del servidor</h1>
                <p>Ha ocurrido un error. Por favor, intenta de nuevo más tarde.</p>
                <a href="/" style="color: #e85a0c; text-decoration: none;">
                    <i class="fas fa-home"></i> Volver al inicio
                </a>
            </div>
            ''', 500
    
    # Limpieza de sesiones de BD
    @app.teardown_appcontext
    def cleanup_db_session_cliente(error):
        """Limpia las sesiones de base de datos al final de cada request"""
        try:
            from config.database import db_config
            db_config.remove_session()
        except Exception:
            pass
    
    # Middleware de seguridad para clientes
    @app.before_request
    def before_request_cliente():
        """Middleware de seguridad y logging para el portal de clientes"""
        from flask import request
        
        # Bloquear acceso a rutas administrativas
        blocked_paths = [
            '/admin', '/dashboard', '/reportes', '/indicadores',
            '/productos/agregar', '/productos/editar', '/productos/eliminar',
            '/clientes/lista', '/clientes/agregar', '/clientes/editar'
        ]
        
        for blocked_path in blocked_paths:
            if request.path.startswith(blocked_path):
                return redirect(url_for('portal_cliente'))
        
        # Log de accesos (solo en desarrollo)
        if not is_production:
            logger.info(f"Cliente accede a: {request.path}")
    
    # Ruta de salud específica para clientes
    @app.route('/health')
    @app.route('/healthz')
    def health_cliente():
        """Endpoint de salud para el portal de clientes"""
        try:
            from config.database import db_config
            health_status, health_message = db_config.health_check()
            
            if health_status:
                # FORZAR LOG para diagnosticar 
                logger.warning("🚨 HEALTH CHECK DESDE CLIENTE PORTAL - SERVICE CORRECTO")
                return {
                    'status': 'healthy',
                    'service': 'FlorezCook Portal de Clientes',
                    'database': 'connected',
                    'timestamp': '2025-06-17'
                }, 200
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'FlorezCook Portal de Clientes',
                    'database': 'disconnected',
                    'error': health_message
                }, 503
        except Exception as e:
            return {
                'status': 'error',
                'service': 'FlorezCook Portal de Clientes',
                'error': str(e)
            }, 500
    
    if not is_production:
        logger.info("🎉 Portal de Clientes FlorezCook configurado exitosamente")
    
    return app

# Crear la instancia de la aplicación cliente a nivel de módulo
app = create_cliente_app()

# Para desarrollo local del portal de clientes
if __name__ == '__main__':
    # Puerto diferente al app principal para evitar conflictos
    port = int(os.environ.get("CLIENTE_PORT", 8081))
    
    print(f"""
    🍽️  FlorezCook Portal de Clientes
    ================================
    🌐 Servidor iniciando en: http://localhost:{port}
    📋 Formulario de pedidos: http://localhost:{port}/pedidos/form
    ⚡ Endpoint de salud: http://localhost:{port}/health
    
    ℹ️  Este es el portal especializado para clientes.
    """)
    
    app.run(host="0.0.0.0", port=port, debug=True)