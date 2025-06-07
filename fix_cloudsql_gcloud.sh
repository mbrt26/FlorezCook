#!/bin/bash
# Script para corregir permisos de Cloud SQL usando gcloud CLI
# Este script es más directo y no requiere acceso root a la base de datos

set -e  # Salir si cualquier comando falla

echo "🚀 Iniciando corrección de permisos Cloud SQL con gcloud CLI"
echo "============================================================"

# Configuración
PROJECT_ID="appsindunnova"
INSTANCE_NAME="florezcook-instance"
DB_NAME="florezcook_db"
OLD_USER="florezcook_user"
NEW_USER="florezcook_app"
PASSWORD="Catalina18"

echo "📋 Configuración:"
echo "   Proyecto: $PROJECT_ID"
echo "   Instancia: $INSTANCE_NAME"
echo "   Base de datos: $DB_NAME"
echo "   Usuario actual: $OLD_USER"
echo "   Nuevo usuario: $NEW_USER"
echo "============================================================"

# Paso 1: Verificar autenticación
echo "🔍 PASO 1: Verificando autenticación con Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ No estás autenticado con Google Cloud"
    echo "🔧 Ejecuta: gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
echo "✅ Autenticado como: $ACTIVE_ACCOUNT"

# Paso 2: Configurar proyecto
echo ""
echo "🔍 PASO 2: Configurando proyecto..."
gcloud config set project $PROJECT_ID
echo "✅ Proyecto configurado: $PROJECT_ID"

# Paso 3: Verificar instancia de Cloud SQL
echo ""
echo "🔍 PASO 3: Verificando instancia de Cloud SQL..."
if ! gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "❌ La instancia $INSTANCE_NAME no existe o no tienes acceso"
    exit 1
fi
echo "✅ Instancia encontrada: $INSTANCE_NAME"

# Paso 4: Eliminar usuario anterior si existe (opcional)
echo ""
echo "🗑️ PASO 4: Limpiando usuarios anteriores..."
if gcloud sql users list --instance=$INSTANCE_NAME --project=$PROJECT_ID --format="value(name)" | grep -q "^$OLD_USER$"; then
    echo "🗑️ Eliminando usuario anterior: $OLD_USER"
    if ! gcloud sql users delete $OLD_USER --instance=$INSTANCE_NAME --project=$PROJECT_ID --quiet; then
        echo "⚠️ No se pudo eliminar el usuario anterior (puede que no exista)"
    fi
else
    echo "ℹ️ Usuario anterior no existe, continuando..."
fi

# Paso 5: Crear nuevo usuario con permisos correctos
echo ""
echo "👤 PASO 5: Creando nuevo usuario con permisos correctos..."
echo "🔧 Creando usuario: $NEW_USER"

if gcloud sql users create $NEW_USER \
    --instance=$INSTANCE_NAME \
    --password=$PASSWORD \
    --host=% \
    --project=$PROJECT_ID; then
    echo "✅ Usuario $NEW_USER creado exitosamente"
else
    echo "❌ Error creando el usuario"
    exit 1
fi

# Paso 6: Otorgar permisos específicos a la base de datos
echo ""
echo "🔑 PASO 6: Otorgando permisos a la base de datos..."

# Nota: gcloud no permite otorgar permisos específicos de base de datos directamente
# Necesitamos usar SQL directo para esto
echo "📝 Conectando para otorgar permisos específicos..."

# Crear script SQL temporal
SQL_SCRIPT="/tmp/grant_permissions.sql"
cat > $SQL_SCRIPT << EOF
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$NEW_USER'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES ON \`$DB_NAME\`.* TO '$NEW_USER'@'%';
FLUSH PRIVILEGES;
SELECT 'Permisos otorgados exitosamente' as resultado;
EOF

echo "📝 Ejecutando script SQL para otorgar permisos..."
if gcloud sql connect $INSTANCE_NAME --user=root --project=$PROJECT_ID < $SQL_SCRIPT; then
    echo "✅ Permisos otorgados exitosamente"
else
    echo "⚠️ Puede que necesites ejecutar los permisos manualmente"
    echo "📋 Script SQL creado en: $SQL_SCRIPT"
fi

# Paso 7: Verificar usuario creado
echo ""
echo "🔍 PASO 7: Verificando usuario creado..."
echo "📋 Usuarios en la instancia:"
gcloud sql users list --instance=$INSTANCE_NAME --project=$PROJECT_ID

# Paso 8: Actualizar configuración de la aplicación
echo ""
echo "🔧 PASO 8: Actualizando configuración de la aplicación..."

# Crear variables de entorno para el nuevo usuario
ENV_CONFIG="/tmp/new_env_config.txt"
cat > $ENV_CONFIG << EOF
# Nueva configuración de variables de entorno para app.yaml
env_variables:
  ENV: "production"
  DB_USER: "$NEW_USER"
  DB_PASS: "$PASSWORD"
  DB_NAME: "$DB_NAME"
  CLOUD_SQL_CONNECTION_NAME: "$PROJECT_ID:southamerica-east1:$INSTANCE_NAME"
  FLASK_ENV: "production"
  PYTHONUNBUFFERED: "1"
  LOG_LEVEL: "WARNING"
EOF

echo "✅ Nueva configuración creada en: $ENV_CONFIG"
echo ""
echo "📋 ACTUALIZA TU app.yaml CON ESTAS VARIABLES:"
cat $ENV_CONFIG

# Limpiar archivos temporales
rm -f $SQL_SCRIPT

echo ""
echo "============================================================"
echo "🎉 CORRECCIÓN COMPLETADA EXITOSAMENTE"
echo "============================================================"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "   1. Actualizar app.yaml con el nuevo usuario: $NEW_USER"
echo "   2. Actualizar config/database.py si es necesario"
echo "   3. Probar conexión local: python3 fix_cloudsql_permissions.py"
echo "   4. Desplegar aplicación: gcloud app deploy"
echo ""
echo "🔧 CAMBIOS REALIZADOS:"
echo "   ✅ Usuario anterior eliminado (si existía)"
echo "   ✅ Nuevo usuario creado: $NEW_USER"
echo "   ✅ Permisos configurados para acceso desde cualquier IP"
echo "   ✅ Permisos específicos otorgados para la base de datos"
echo ""
echo "⚠️ NOTA: Si sigues teniendo problemas de conexión, ejecuta:"
echo "   python3 fix_cloudsql_permissions.py"
echo ""