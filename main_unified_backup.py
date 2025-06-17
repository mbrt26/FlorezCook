#!/usr/bin/env python3
"""
FlorezCook - Aplicación Principal Unificada
Maneja tanto la aplicación completa como el portal de clientes
"""
import os
import logging
from flask import Flask, request, redirect, url_for

# Configurar logging para producción
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración de la aplicación
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['ENV'] = os.environ.get('ENV', 'development')
    
    # Registrar rutas básicas
    register_basic_routes(app)
    
    return app

def register_basic_routes(app):
    """Registra las rutas básicas y el routing inteligente"""
    
    @app.before_request
    def route_handler():
        """Maneja el routing entre portal de clientes y aplicación completa"""
        host = request.host.lower()
        path = request.path.lower()
        
        # Detectar si es portal de clientes
        is_cliente_portal = (
            'cliente' in host or 
            'portal' in host or 
            path.startswith('/cliente')
        )
        
        if is_cliente_portal and path not in ['/health', '/favicon.ico']:
            # Redirigir todo el tráfico del portal de clientes a la app cliente
            return handle_cliente_request()
        
        # Continuar con el flujo normal para otras rutas
        return None
    
    def handle_cliente_request():
        """Maneja todas las requests del portal de clientes"""
        try:
            from app_cliente import app as cliente_app
            
            # Obtener el path sin el prefijo /cliente
            path = request.path
            if path.startswith('/cliente'):
                path = path[8:]  # Remover '/cliente'
            if not path:
                path = '/'
            
            # Crear un contexto de request simplificado para la app cliente
            with cliente_app.test_request_context(path=path, method=request.method):
                try:
                    # Buscar la ruta en la aplicación cliente
                    endpoint, values = cliente_app.url_map.bind('localhost').match(path, request.method)
                    
                    # Ejecutar la vista correspondiente
                    view_function = cliente_app.view_functions[endpoint]
                    response = view_function(**values)
                    
                    return response
                    
                except Exception as e:
                    # Si hay un error específico, intentar la ruta raíz de la app cliente
                    try:
                        with cliente_app.app_context():
                            return cliente_app.view_functions['portal_cliente']()
                    except:
                        # Fallback a página básica si todo falla
                        return '''
                        <!DOCTYPE html>
                        <html lang="es">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>FlorezCook - Portal de Clientes</title>
                            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                        </head>
                        <body>
                            <div class="container mt-5">
                                <h1>🍽️ Portal de Clientes - FlorezCook</h1>
                                <p>Bienvenido al portal de clientes</p>
                                <div class="alert alert-info">
                                    <p>El portal de clientes está en mantenimiento.</p>
                                    <p>Path solicitado: ''' + path + '''</p>
                                    <p>Error: ''' + str(e) + '''</p>
                                </div>
                                <a href="/" class="btn btn-primary">Ir al Sistema Principal</a>
                            </div>
                        </body>
                        </html>
                        '''
                        
        except ImportError:
            # Si no se puede importar app_cliente
            return '''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>FlorezCook - Portal de Clientes</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <h1>🍽️ Portal de Clientes - FlorezCook</h1>
                    <div class="alert alert-warning">
                        <p>El portal de clientes no está disponible en este momento.</p>
                        <p>Por favor, contacta al administrador.</p>
                    </div>
                    <a href="/" class="btn btn-primary">Ir al Sistema Principal</a>
                </div>
            </body>
            </html>
            ''', 503
    
    # Ruta principal
    @app.route('/')
    def index():
        """Página principal que redirige según el contexto"""
        host = request.host.lower()
        
        if 'cliente' in host or 'portal' in host:
            # Portal de clientes - delegar completamente a app_cliente
            return handle_cliente_request()
        else:
            # Aplicación completa - delegar a la app principal
            try:
                from app import app as main_app
                with main_app.app_context():
                    return main_app.view_functions['home']()
            except (ImportError, KeyError):
                return '''
                <h1>🍽️ FlorezCook - Sistema de Gestión</h1>
                <p>¡Bienvenido al sistema de gestión de FlorezCook!</p>
                <a href="/health">🔍 Estado del Sistema</a>
                '''
    
    # Rutas específicas del portal de clientes
    @app.route('/cliente')
    @app.route('/cliente/')
    @app.route('/cliente/<path:subpath>')
    def cliente_portal(subpath=''):
        """Todas las rutas del portal de clientes"""
        return handle_cliente_request()
    
    # Ruta de salud para monitoreo
    @app.route('/health')
    def health():
        """Endpoint de salud para App Engine"""
        return {'status': 'healthy', 'service': 'florezcook-unified'}, 200
    
    # Proxy para rutas de la aplicación principal
    @app.route('/<path:path>')
    def proxy_to_main_app(path):
        """Proxy todas las demás rutas a la aplicación principal"""
        # Evitar conflicto con rutas de cliente
        if path.startswith('cliente'):
            return handle_cliente_request()
            
        try:
            from app import app as main_app
            
            # Buscar la ruta en la aplicación principal
            with main_app.test_request_context('/' + path, method=request.method):
                try:
                    endpoint, values = main_app.url_map.bind(request.environ.get('SERVER_NAME', 'localhost')).match('/' + path, request.method)
                    if endpoint in main_app.view_functions:
                        return main_app.view_functions[endpoint](**values)
                except Exception:
                    pass
            
            # Si no se encuentra la ruta, devolver 404
            return '''
            <h2>🔍 Página No Encontrada</h2>
            <p>La página que buscas no existe.</p>
            <a href="/">🏠 Volver al inicio</a>
            ''', 404
            
        except ImportError:
            return '''
            <h2>⚠️ Error de Configuración</h2>
            <p>No se pudo cargar la aplicación principal.</p>
            <a href="/">🏠 Volver al inicio</a>
            ''', 500

# Crear la aplicación para App Engine
app = create_app()

if __name__ == '__main__':
    # Para desarrollo local
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('ENV', 'development') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
