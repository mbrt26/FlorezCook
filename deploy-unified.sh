#!/bin/bash
# Script de Despliegue Unificado para FlorezCook
# Despliega tanto la aplicación completa como el portal de clientes en un solo servicio

set -e  # Salir si hay errores

echo "🚀 Iniciando despliegue unificado de FlorezCook..."

# Configuraciones
PROJECT_ID="appsindunnova"
SERVICE_NAME="florezcook"
REGION="southamerica-east1"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Verificar que estamos en el directorio correcto
if [ ! -f "app.yaml" ]; then
    error "No se encontró app.yaml. Ejecute este script desde el directorio raíz del proyecto."
fi

# Verificar que gcloud está instalado y configurado
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI no está instalado. Instálelo desde https://cloud.google.com/sdk/"
fi

# Verificar autenticación
log "Verificando autenticación con Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log "Iniciando autenticación..."
    gcloud auth login
fi

# Configurar proyecto
log "Configurando proyecto: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Verificar que la Cloud SQL instance existe
log "Verificando Cloud SQL instance..."
if ! gcloud sql instances describe florezcook-instance --region=$REGION &> /dev/null; then
    warning "La instancia de Cloud SQL 'florezcook-instance' no existe o no está accesible."
    echo "¿Desea continuar con el despliegue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        error "Despliegue cancelado por el usuario."
    fi
fi

# Crear backup del app.yaml actual
log "Creando backup de configuración..."
cp app.yaml "app.yaml.backup-$(date +%Y%m%d_%H%M%S)"

# Validar dependencias
log "Verificando dependencias de Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --dry-run &> /dev/null || warning "Algunas dependencias podrían fallar en App Engine"
fi

# Pre-deployment checks
log "Ejecutando verificaciones pre-despliegue..."

# Verificar que los archivos principales existen
required_files=("main.py" "app.py" "app_cliente.py" "models.py" "business_logic.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        error "Archivo requerido no encontrado: $file"
    fi
done

# Verificar estructura de templates
if [ ! -d "templates" ]; then
    error "Directorio 'templates' no encontrado"
fi

required_templates=("base.html" "base_cliente.html" "pedido_form.html" "pedido_form_cliente.html")
for template in "${required_templates[@]}"; do
    if [ ! -f "templates/$template" ]; then
        warning "Template no encontrado: templates/$template"
    fi
done

# Test de sintaxis Python
log "Verificando sintaxis de Python..."
python3 -m py_compile main.py || error "Error de sintaxis en main.py"
python3 -m py_compile app.py || error "Error de sintaxis en app.py"
python3 -m py_compile app_cliente.py || error "Error de sintaxis en app_cliente.py"

success "Verificaciones pre-despliegue completadas ✓"

# Preguntar confirmación antes del despliegue
echo ""
echo "========================== RESUMEN DEL DESPLIEGUE =========================="
echo "Proyecto: $PROJECT_ID"
echo "Servicio: $SERVICE_NAME (default)"
echo "Región: $REGION"
echo "Aplicaciones: Completa + Portal de Clientes (unificadas)"
echo "Acceso:"
echo "  - App Completa: https://florezcook.appspot.com"
echo "  - Portal Clientes: https://cliente.florezcook.appspot.com"
echo "  - Portal Clientes Alt: https://florezcook.appspot.com/cliente"
echo "=========================================================================="
echo ""
echo "¿Desea continuar con el despliegue? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    log "Despliegue cancelado por el usuario."
    exit 0
fi

# Desplegar la aplicación
log "Desplegando aplicación a App Engine (servicio: $SERVICE_NAME)..."
gcloud app deploy app.yaml --quiet --promote --stop-previous-version

# Desplegar dispatch rules
log "Desplegando reglas de dispatch..."
gcloud app deploy dispatch.yaml --quiet

# Verificar el despliegue
log "Verificando despliegue..."
MAIN_URL="https://florezcook-dot-appsindunnova.appspot.com"
CLIENT_URL="https://cliente.florezcook.appspot.com"

# Esperar un momento para que el servicio esté listo
sleep 10

# Test de conectividad
log "Probando conectividad..."
if curl -s --max-time 30 "$MAIN_URL/health" | grep -q "healthy"; then
    success "Aplicación principal está respondiendo ✓"
else
    warning "La aplicación principal podría estar iniciándose aún"
fi

# Mostrar información final
echo ""
echo "🎉 ¡DESPLIEGUE COMPLETADO!"
echo ""
echo "URLs de Acceso:"
echo "=========================="
echo "📱 Aplicación Completa (Administración):"
echo "   $MAIN_URL"
echo ""
echo "👥 Portal de Clientes:"
echo "   $CLIENT_URL"
echo "   $MAIN_URL/cliente"
echo ""
echo "🔧 Endpoints útiles:"
echo "   Health Check: $MAIN_URL/health"
echo "   API: $MAIN_URL/api/"
echo ""
echo "📊 Monitoreo:"
echo "   Logs: gcloud app logs tail -s $SERVICE_NAME"
echo "   Métricas: https://console.cloud.google.com/appengine"
echo ""

# Abrir URLs en el navegador (opcional)
echo "¿Desea abrir las aplicaciones en el navegador? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open "$MAIN_URL"
        open "$CLIENT_URL"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$MAIN_URL"
        xdg-open "$CLIENT_URL"
    else
        log "Abra manualmente las URLs mostradas arriba"
    fi
fi

success "Script de despliegue completado exitosamente 🚀"