#!/bin/bash

# Script para desplegar la aplicación en Google Cloud Platform

# Colores para la salida
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes de éxito
success() {
    echo -e "${GREEN}[ÉXITO]${NC} $1"
}

# Función para imprimir advertencias
warning() {
    echo -e "${YELLOW}[ADVERTENCIA]${NC} $1"
}

# Función para imprimir errores
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Verificar que estemos en el directorio correcto
if [ ! -f "app.py" ] || [ ! -f "app.yaml" ]; then
    error "No se encuentra el archivo app.py o app.yaml. Asegúrate de estar en el directorio raíz del proyecto."
fi

# Verificar que gcloud esté instalado
if ! command -v gcloud &> /dev/null; then
    error "Google Cloud SDK no está instalado. Por favor, instálalo desde https://cloud.google.com/sdk/install"
fi

# Verificar que el usuario esté autenticado
echo "Verificando autenticación con Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' &> /dev/null; then
    warning "No estás autenticado en Google Cloud. Iniciando autenticación..."
    gcloud auth login
fi

# Configurar el proyecto
echo "Configurando el proyecto de Google Cloud..."
PROJECT_ID=$(gcloud config get-value project 2> /dev/null)

if [ -z "$PROJECT_ID" ]; then
    warning "No se ha configurado un proyecto de Google Cloud."
    echo "Proyectos disponibles:"
    gcloud projects list --format="value(projectId)"
    echo ""
    read -p "Ingresa el ID del proyecto: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
    success "Proyecto configurado: $PROJECT_ID"
else
    echo "Usando proyecto: $PROJECT_ID"
fi

# Verificar que las APIs necesarias estén habilitadas
echo "Verificando APIs habilitadas..."
REQUIRED_APIS=(
    "appengine.googleapis.com"
    "sqladmin.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
)

for API in "${REQUIRED_APIS[@]}"; do
    if ! gcloud services list --enabled --filter="NAME:$API" --format='value(NAME)' | grep -q "$API"; then
        warning "La API $API no está habilitada. Habilitando..."
        gcloud services enable "$API"
        success "API $API habilitada."
    else
        echo "API $API ya está habilitada."
    fi
done

# Verificar que la instancia de Cloud SQL exista
echo "Verificando instancia de Cloud SQL..."
INSTANCE_NAME="florezcook-db"
if ! gcloud sql instances describe "$INSTANCE_NAME" --format="value(name)" &> /dev/null; then
    error "No se encontró la instancia de Cloud SQL '$INSTANCE_NAME'. Por favor, crea la instancia primero."
else
    echo "Instancia de Cloud SQL encontrada: $INSTANCE_NAME"
fi

# Configurar variables de entorno para la base de datos
echo "Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    warning "No se encontró el archivo .env. Creando uno con valores por defecto..."
    cat > .env <<EOL
# Configuración de la aplicación
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Configuración de la base de datos
DB_USER=root
DB_PASS=your_secure_password  # Cambia esto
DB_NAME=florezcook_db
DB_HOST=localhost

# Configuración de Cloud SQL
CLOUD_SQL_CONNECTION_NAME=$PROJECT_ID:us-central1:$INSTANCE_NAME
ENV=production

# Configuración de Google Cloud
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
EOL
    warning "Se ha creado un archivo .env con valores por defecto. Por favor, revísalo y actualiza las credenciales."
    read -p "Presiona Enter para continuar o Ctrl+C para cancelar..."
else
    echo "Archivo .env encontrado."
fi

# Instalar dependencias
echo "Instalando dependencias..."
pip3 install -r requirements.txt

# Desplegar la aplicación con tiempo de espera extendido
echo "Iniciando despliegue en Google App Engine..."
gcloud app deploy app.yaml --quiet --timeout=20m

# Mostrar URL de la aplicación desplegada
APP_URL=$(gcloud app browse --no-launch-browser)
success "¡Despliegue completado con éxito!"
echo "Tu aplicación está disponible en: $APP_URL"
echo ""
echo "Para ver los logs en tiempo real, ejecuta:"
echo "gcloud app logs tail -s default"
echo ""
echo "Para abrir la aplicación en tu navegador:"
echo "gcloud app browse"
