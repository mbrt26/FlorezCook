from flask import Blueprint, jsonify, current_app
from config.database import db_config

health_bp = Blueprint('health', __name__)

@health_bp.route('/healthz')
def liveness():
    """Endpoint de liveness check para Kubernetes"""
    try:
        is_healthy, message = db_config.health_check()
        if is_healthy:
            return jsonify({"status": "healthy", "message": message}), 200
        else:
            return jsonify({"status": "unhealthy", "error": message}), 500
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@health_bp.route('/readiness')
def readiness():
    """Endpoint de readiness check para Kubernetes"""
    try:
        is_healthy, message = db_config.health_check()
        if is_healthy:
            return jsonify({"status": "ready", "message": message}), 200
        else:
            return jsonify({"status": "not ready", "error": message}), 503
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {e}")
        return jsonify({"status": "not ready", "error": str(e)}), 503