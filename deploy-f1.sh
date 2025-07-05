#!/bin/bash
# Script de despliegue para FlorezCook con configuración F1

echo "🚀 Iniciando despliegue de FlorezCook con configuración F1..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "app-f1.yaml" ]; then
    echo "❌ Error: No se encuentra app-f1.yaml"
    echo "Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

# Mostrar resumen de cambios
echo "📋 Cambios a desplegar:"
echo "  ✅ Zona horaria Colombia (UTC-5)"
echo "  ✅ Sábado como día hábil"
echo "  ✅ Campo NIT mejorado en móviles"
echo "  ✅ Configuración F1 (ahorro ~$100/mes)"
echo ""

# Confirmar despliegue
read -p "¿Continuar con el despliegue? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Despliegue cancelado"
    exit 1
fi

# Push a git
echo ""
echo "📤 Subiendo cambios a Git..."
git push origin main

# Desplegar a App Engine
echo ""
echo "☁️  Desplegando a Google App Engine..."
gcloud app deploy app-f1.yaml \
    --project=appsindunnova \
    --version=$(date +%Y%m%d-%H%M%S) \
    --promote \
    --quiet

# Verificar el despliegue
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Despliegue exitoso!"
    echo ""
    echo "🔗 URLs de acceso:"
    echo "  - Principal: https://florezcook-dot-appsindunnova.rj.r.appspot.com"
    echo "  - Cliente: https://cliente-dot-florezcook-dot-appsindunnova.rj.r.appspot.com"
    echo ""
    echo "📊 Monitoreo:"
    echo "  - Logs: gcloud app logs tail -s florezcook"
    echo "  - Métricas: https://console.cloud.google.com/appengine"
    echo ""
    echo "💡 Recuerda:"
    echo "  - La primera request puede ser lenta (cold start)"
    echo "  - Monitorea el rendimiento las primeras horas"
    echo "  - El ahorro se verá reflejado en la próxima factura"
else
    echo ""
    echo "❌ Error en el despliegue"
    echo "Revisa los logs con: gcloud app logs read"
fi