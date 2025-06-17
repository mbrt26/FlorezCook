#!/usr/bin/env python3
"""
FlorezCook - App Engine Main Entry Point (Aplicación Principal)
"""

# Para la aplicación principal, usar el create_app pattern
from app import create_app

# Crear la instancia de la aplicación principal
app = create_app()

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)