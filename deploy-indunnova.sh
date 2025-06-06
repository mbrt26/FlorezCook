#!/bin/bash

# Script de despliegue para FlorezCook en el proyecto appsindunnova
# Como servicio separado

set -e

echo "🚀 Iniciando despliegue de FlorezCook en appsindunnova..."

# Verificar que gcloud esté configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI no está instalado"
    echo "Instala Google Cloud SDK desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configurar el proyecto
PROJECT_ID="appsindunnova"
SERVICE_NAME="florezcook"
REGION="southamerica-east1"

echo "📋 Configurando proyecto: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Verificar autenticación
echo "🔐 Verificando autenticación..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ No hay cuentas autenticadas"
    echo "Ejecuta: gcloud auth login"
    exit 1
fi

# Habilitar APIs necesarias
echo "🔧 Habilitando APIs necesarias..."
gcloud services enable appengine.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# Verificar que App Engine esté inicializado
echo "🏗️ Verificando App Engine..."
if ! gcloud app describe >/dev/null 2>&1; then
    echo "⚠️ App Engine no está inicializado en este proyecto"
    echo "Inicializando App Engine en región $REGION..."
    gcloud app create --region=$REGION
fi

echo "📦 Desplegando aplicación como servicio '$SERVICE_NAME'..."

# Desplegar usando el archivo de configuración específico
gcloud app deploy app-indunnova.yaml \
    --project=$PROJECT_ID \
    --version=v$(date +%Y%m%d-%H%M%S) \
    --promote \
    --stop-previous-version

echo "✅ ¡Despliegue completado!"
echo ""
echo "🌐 URLs de acceso:"
echo "   Servicio FlorezCook: https://$SERVICE_NAME-dot-$PROJECT_ID.appspot.com"
echo "   Panel de App Engine: https://console.cloud.google.com/appengine/services?project=$PROJECT_ID"
echo ""
echo "📊 Comandos útiles:"
echo "   Ver logs: gcloud app logs tail -s $SERVICE_NAME --project=$PROJECT_ID"
echo "   Ver servicios: gcloud app services list --project=$PROJECT_ID"
echo "   Abrir en navegador: gcloud app browse -s $SERVICE_NAME --project=$PROJECT_ID"