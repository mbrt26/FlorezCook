#!/usr/bin/env python3
"""
FlorezCook - Portal de Clientes EXCLUSIVO
Esta versión de main.py es específica para el servicio cliente
"""

import os
import logging
from flask import Flask, render_template, redirect, url_for, request, g, jsonify

# Configurar logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Crear aplicación Flask específica para clientes
app = Flask(__name__)

# Configuración específica para portal de clientes
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'florezcook-cliente-portal-2025-secure'),
    'IS_CLIENTE_PORTAL': True,
    'ENV': os.environ.get('ENV', 'production'),
    'DEBUG': False
})

# Middleware OBLIGATORIO para marcar como portal de clientes
@app.before_request
def force_cliente_portal():
    """FORZAR contexto de portal de clientes"""
    g.is_cliente_portal = True
    g.template_base = 'base_cliente.html'
    app.config['IS_CLIENTE_PORTAL'] = True

# Registrar rutas necesarias para clientes
try:
    from routes.pedidos import pedidos_bp
    app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
    logger.warning("✅ Rutas de pedidos registradas en portal cliente")
except Exception as e:
    logger.error(f"❌ Error registrando rutas de pedidos: {e}")

# API para búsqueda de productos (necesaria para pedidos)
@app.route('/productos/api/buscar')
def buscar_productos_api():
    """API para buscar productos en el portal de clientes"""
    try:
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
    except Exception as e:
        logger.error(f"Error en búsqueda de productos: {e}")
        return jsonify([])

# API para búsqueda de clientes (necesaria para pedidos)
@app.route('/api/clientes/buscar')
def buscar_clientes_api():
    """API para buscar clientes en el portal de clientes"""
    try:
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
        logger.error(f"Error en búsqueda de clientes: {e}")
        return jsonify({'existe': False})

# Página principal del portal de clientes (SIN módulos administrativos)
@app.route('/')
def portal_cliente():
    """Página principal EXCLUSIVA del portal de clientes"""
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; }
        .hero-section { background: linear-gradient(135deg, var(--florez-primary), #d04c06); color: white; padding: 4rem 0; }
        .btn-florez { background-color: var(--florez-primary); border-color: var(--florez-primary); color: white; }
        .btn-florez:hover { background-color: #d04c06; border-color: #d04c06; color: white; }
        .card { box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1); border: none; border-radius: 8px; }
    </style>
</head>
<body>
    <!-- SIN BARRA DE NAVEGACIÓN ADMINISTRATIVA -->
    
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
    
    <div class="container my-5">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <div class="card text-center">
                    <div class="card-body p-5">
                        <i class="fas fa-shopping-cart fa-4x text-primary mb-4"></i>
                        <h3 class="card-title">Crear Nuevo Pedido</h3>
                        <p class="card-text">Accede a nuestro sistema de pedidos optimizado para una experiencia rápida y sencilla.</p>
                        <a href="/pedidos/form" class="btn btn-florez btn-lg">
                            <i class="fas fa-plus me-2"></i>
                            Comenzar Pedido
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-dark text-light py-4 mt-5">
        <div class="container text-center">
            <p class="mb-0">&copy; 2025 FlorezCook. Portal de Clientes - Todos los derechos reservados.</p>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

# Health check específico para clientes
@app.route('/health')
@app.route('/healthz')
def health():
    """Health check del portal de clientes"""
    return {
        'status': 'healthy',
        'service': 'FlorezCook Portal de Clientes EXCLUSIVO',
        'version': '2025-06-17-fixed',
        'is_cliente_portal': True
    }, 200

# Bloquear acceso a rutas administrativas
@app.route('/productos')
@app.route('/clientes')
@app.route('/reportes')
@app.route('/indicadores')
@app.route('/admin')
def bloquear_admin():
    """Bloquear acceso a módulos administrativos"""
    return redirect(url_for('portal_cliente'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8081))
    logger.warning(f"🍽️ Portal de Clientes EXCLUSIVO iniciando en puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)