#!/usr/bin/env python3
"""
FlorezCook - Portal de Clientes (Main Entry Point)
Entry point específico para el servicio de clientes en App Engine
"""

# Importar la aplicación cliente
from app_cliente import app

# Para App Engine - la variable debe llamarse 'app'
# Esta es la única diferencia con app_cliente.py

if __name__ == '__main__':
    # Para desarrollo local del portal de clientes
    import os
    port = int(os.environ.get("CLIENTE_PORT", 8081))
    
    print(f"""
    🍽️  FlorezCook Portal de Clientes (Main Entry)
    ============================================
    🌐 Servidor iniciando en: http://localhost:{port}
    📋 Formulario de pedidos: http://localhost:{port}/pedidos/form
    ⚡ Endpoint de salud: http://localhost:{port}/health
    
    ℹ️  Este es el portal especializado para clientes (via main_cliente.py).
    """)
    
    app.run(host="0.0.0.0", port=port, debug=True)