import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user, login_user
from config.database import db_config
from routes.health import health_bp
from routes.pedidos import pedidos_bp
from routes.productos import productos_bp
from routes.clientes import clientes_bp, api_clientes_bp
from routes.reportes import reportes_bp
from dotenv import load_dotenv
from models import User

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    # Por ahora, simplemente creamos un usuario superadmin
    # En un futuro, esto debería cargar el usuario desde la base de datos
    return User(user_id, role='superadmin')

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'florezcook-secret-key')
    
    # Inicializar Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(api_clientes_bp)
    app.register_blueprint(reportes_bp)
    
    # Autenticar automáticamente al usuario como superadmin
    @app.before_request
    def auto_login():
        if not current_user.is_authenticated:
            user = User(1, role='superadmin')
            login_user(user)

    # Ruta principal
    @app.route('/')
    def index():
        """Redirige a la página principal de pedidos"""
        return redirect(url_for('pedidos.form'))
        
    # Redirección para importar productos
    @app.route('/importar-productos')
    def importar_productos_redirect():
        return redirect(url_for('productos.importar'))

    # Redirección para importar clientes
    @app.route('/importar-clientes')
    def importar_clientes_redirect():
        return redirect(url_for('clientes.importar'))

    # Manejar limpieza de sesiones de base de datos
    @app.teardown_appcontext
    def remove_session(exception=None):
        """Limpia las sesiones de base de datos al final de cada request"""
        db = db_config.get_session()
        if db is not None:
            db.close()

    return app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
