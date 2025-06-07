from flask import Blueprint, jsonify, current_app
from config.database import db_config

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
@health_bp.route('/healthz')
def liveness():
    """Endpoint de liveness check - siempre devuelve OK"""
    # Para liveness, solo verificamos que la aplicación esté funcionando
    # No dependemos de la base de datos para evitar fallos durante el arranque
    return jsonify({"status": "healthy", "message": "Application is running"}), 200

@health_bp.route('/readiness')
def readiness():
    """Endpoint de readiness check - verifica la base de datos"""
    try:
        is_healthy, message = db_config.health_check()
        if is_healthy:
            return jsonify({"status": "ready", "message": message}), 200
        else:
            return jsonify({"status": "not ready", "error": message}), 503
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {e}")
        return jsonify({"status": "not ready", "error": str(e)}), 503