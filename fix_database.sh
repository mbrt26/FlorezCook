#!/bin/bash
"""
Script para ejecutar la actualización de la base de datos desde Google Cloud Shell
"""

echo "=== Actualizando estructura de la base de datos FlorezCook ==="
echo "Fecha: $(date)"
echo ""

# Configurar variables de entorno para Cloud SQL
export DB_USER="florezcook_user"
export DB_PASS="florezcook2025"
export DB_NAME="florezcook_db"
export CLOUD_SQL_CONNECTION_NAME="appsindunnova:southamerica-east1:florezcook-instance"

echo "Variables de entorno configuradas:"
echo "- DB_USER: $DB_USER"
echo "- DB_NAME: $DB_NAME"
echo "- CLOUD_SQL_CONNECTION_NAME: $CLOUD_SQL_CONNECTION_NAME"
echo ""

# Verificar que Python esté disponible
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no está disponible"
    exit 1
fi

# Instalar dependencias necesarias
echo "Instalando dependencias..."
pip3 install sqlalchemy pymysql

echo ""
echo "Ejecutando actualización de la base de datos..."
python3 update_database_schema.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Actualización completada exitosamente"
    echo "La columna 'descripcion' ha sido agregada a la tabla productos"
else
    echo ""
    echo "❌ Error en la actualización de la base de datos"
    exit 1
fi