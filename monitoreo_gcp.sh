#!/bin/bash
# Script de Monitoreo para FlorezCook en GCP
# Ejecuta este script para obtener métricas de rendimiento

echo "📊 MÉTRICAS DE RENDIMIENTO - $(date)"
echo "============================================"

# 1. Estado de la aplicación
echo "🌐 Estado de la aplicación:"
curl -s -o /dev/null -w "Tiempo de respuesta: %{time_total}s - Status: %{http_code}\n" \
    https://rgd-aire-dot-appsindunnova.rj.r.appspot.com/health

# 2. Logs recientes de App Engine
echo "\n📝 Logs recientes (últimos 5 minutos):"
gcloud app logs tail --service=default --lines=10

# 3. Métricas de Cloud SQL
echo "\n🗄️ Estado de Cloud SQL:"
gcloud sql instances describe florezcook-instance --format="table(state,backendType,ipAddresses[0].ipAddress)"

# 4. Uso de CPU y memoria
echo "\n💻 Métricas de recursos:"
gcloud monitoring metrics list --filter="resource.type=gae_app" --limit=5

echo "\n✅ Monitoreo completado"
