#!/usr/bin/env python3
"""
FlorezCook - App Engine Main Entry Point
Detecta automáticamente si es servicio de clientes o aplicación principal
"""

import os

# Detectar el servicio por variables de entorno o servicio
service = os.environ.get('GAE_SERVICE', 'default')

if service == 'cliente':
    # Para el servicio de clientes, importar la aplicación cliente
    from app_cliente import app
else:
    # Para el servicio principal, importar la aplicación principal
    from app import create_app
    app = create_app()

# App Engine busca automáticamente la variable 'app' en main.py