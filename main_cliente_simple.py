#!/usr/bin/env python3
"""
FlorezCook - Portal de Clientes (Main Simple)
Entry point simplificado y confiable para el portal de clientes
"""

import os
import logging
from flask import Flask, render_template, redirect, url_for, request, g

# Configurar logging básico
logging.basicConfig(level=logging.WARNING)

def create_cliente_app():
    """Crea una aplicación Flask simplificada específica para clientes"""
    app = Flask(__name__)
    
    # Configuración básica
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'florezcook-cliente-portal-2025-secure'),
        'IS_CLIENTE_PORTAL': True,
        'ENV': os.environ.get('ENV', 'production'),
        'DEBUG': False
    })
    
    # Middleware para marcar como portal de clientes
    @app.before_request
    def setup_cliente_context():
        g.is_cliente_portal = True
        g.template_base = 'base_cliente.html'
    
    # Importar y registrar solo las rutas necesarias
    try:
        from routes.pedidos import pedidos_bp
        app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
        
        # API simple para productos (sin importar toda la ruta)
        @app.route('/productos/api/buscar')
        def buscar_productos_api():
            from flask import request, jsonify
            from config.database import db_config
            from models import Producto
            
            termino = request.args.get('q', '').strip()
            limit = int(request.args.get('limit', 10))
            
            if len(termino) < 1:
                return jsonify([])
            
            db = db_config.get_session()
            try:
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
                    'categoria_linea': p.categoria_linea or ''
                } for p in productos])
            finally:
                db.close()
        
        # API simple para clientes
        @app.route('/api/clientes/buscar')
        def buscar_clientes_api():
            from flask import request, jsonify
            from config.database import db_config
            from models import Cliente
            
            nit = request.args.get('nit', '').strip()
            
            if not nit:
                return jsonify({'existe': False})
            
            db = db_config.get_session()
            try:
                cliente = db.query(Cliente).filter(
                    Cliente.numero_identificacion == nit
                ).first()
                
                if cliente:
                    return jsonify({
                        'existe': True,
                        'id': cliente.id,
                        'nombre_comercial': cliente.nombre_comercial,
                        'tipo_identificacion': cliente.tipo_identificacion,
                        'numero_identificacion': cliente.numero_identificacion,
                        'direccion': cliente.direccion,
                        'ciudad': cliente.ciudad,
                        'departamento': cliente.departamento
                    })
                else:
                    return jsonify({'existe': False})
            finally:
                db.close()
        
    except Exception as e:
        logging.error(f"Error registrando rutas: {e}")
    
    # Página principal del portal de clientes
    @app.route('/')
    def portal_cliente():
        """Página principal simplificada del portal de clientes"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlorezCook - Portal de Clientes</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --florez-primary: #e85a0c; }
        .hero-section { background: linear-gradient(135deg, var(--florez-primary), #d04c06); color: white; padding: 4rem 0; }
        .btn-florez { background-color: var(--florez-primary); border-color: var(--florez-primary); color: white; }
        .btn-florez:hover { background-color: #d04c06; border-color: #d04c06; color: white; }
    </style>
</head>
<body>
    <div class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 mb-4">
                <i class="fas fa-utensils me-3"></i>
                Portal de Clientes FlorezCook
            </h1>
            <p class="lead mb-4">Realiza tus pedidos de forma rápida y sencilla</p>
            <a href="/pedidos/form" class="btn btn-light btn-lg">
                <i class="fas fa-clipboard-list me-2"></i>
                Hacer un Pedido
            </a>
        </div>
    </div>
    <div class="container my-5 text-center">
        <h3 class="mb-4">¿Listo para hacer tu pedido?</h3>
        <a href="/pedidos/form" class="btn btn-florez btn-lg">
            <i class="fas fa-play me-2"></i>
            Comenzar Ahora
        </a>
    </div>
    <footer class="bg-light py-4 mt-5">
        <div class="container text-center">
            <p class="mb-0">&copy; 2025 FlorezCook. Portal de Clientes - Todos los derechos reservados.</p>
        </div>
    </footer>
</body>
</html>'''
    
    # Health check
    @app.route('/health')
    @app.route('/healthz')
    def health():
        return {
            'status': 'healthy',
            'service': 'FlorezCook Portal de Clientes (Simple)',
            'timestamp': '2025-06-17'
        }, 200
    
    return app

# Crear la aplicación
app = create_cliente_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port, debug=False)