#!/usr/bin/env python3
"""
Test simple para el portal de clientes
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def test():
    return "TEST CLIENTE PORTAL FUNCIONANDO - VERSION SIMPLE"

@app.route('/health')
def health():
    return {"service": "TEST CLIENTE PORTAL", "status": "healthy"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)