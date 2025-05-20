"""
Punto de entrada principal para la aplicación FlorezCook en producción.
"""
import os
from app import app, get_db_engine
from models import Base

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    try:
        engine = get_db_engine()
        if engine is not None:
            print("Creando tablas en la base de datos...")
            Base.metadata.create_all(bind=engine)
            print("¡Base de datos inicializada correctamente!")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise

def create_app():
    """Crea y configura la aplicación Flask."""
    with app.app_context():
        # Inicializar la base de datos
        init_db()
    return app

# Inicializar la base de datos al iniciar la aplicación
if os.getenv('ENV') == 'production':
    print("Entorno de producción detectado. Inicializando base de datos...")

# Para ejecutar localmente
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
