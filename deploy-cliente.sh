#!/bin/bash

echo "🍽️  Desplegando Portal de Clientes FlorezCook"
echo "=============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "app_cliente.py" ]; then
    echo "❌ Error: No se encuentra app_cliente.py"
    echo "   Asegúrate de estar en el directorio del proyecto FlorezCook"
    exit 1
fi

# Verificar que gcloud está configurado
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI no está instalado"
    exit 1
fi

echo "📋 Verificando configuración..."

# Mostrar información del proyecto
PROJECT_ID=$(gcloud config get-value project)
echo "   Proyecto: $PROJECT_ID"

# Verificar archivos necesarios
echo "📁 Verificando archivos..."
if [ -f "app-cliente.yaml" ]; then
    echo "   ✅ app-cliente.yaml encontrado"
else
    echo "   ❌ app-cliente.yaml no encontrado"
    exit 1
fi

if [ -f "app_cliente.py" ]; then
    echo "   ✅ app_cliente.py encontrado"
else
    echo "   ❌ app_cliente.py no encontrado"
    exit 1
fi

echo ""
echo "🚀 Iniciando despliegue del Portal de Clientes..."
echo ""

# Desplegar la aplicación
gcloud app deploy app-cliente.yaml --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ¡Portal de Clientes desplegado exitosamente!"
    echo ""
    echo "📍 URLs del Portal de Clientes:"
    echo "   Portal Principal: https://cliente-dot-$PROJECT_ID.appspot.com"
    echo "   Formulario Pedidos: https://cliente-dot-$PROJECT_ID.appspot.com/pedidos/form"
    echo "   Health Check: https://cliente-dot-$PROJECT_ID.appspot.com/health"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   Ver logs: gcloud app logs tail -s cliente"
    echo "   Abrir en navegador: gcloud app browse -s cliente"
    echo ""
else
    echo "❌ Error durante el despliegue"
    exit 1
fi