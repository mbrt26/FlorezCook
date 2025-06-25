#!/usr/bin/env python3
"""
FlorezCook - Aplicación Principal
Entry point para la aplicación completa de FlorezCook en App Engine
"""

from app import create_app

# Crear la aplicación usando la factory function
app = create_app()

if __name__ == '__main__':
    # Para desarrollo local
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)