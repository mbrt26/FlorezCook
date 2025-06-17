# FlorezCook - Guía de Despliegue Unificado

## 🚀 Arquitectura de Despliegue

### Estrategia Implementada: **1 Servicio, 2 Interfaces**

- **Un solo servicio de App Engine** que maneja ambas aplicaciones
- **Routing inteligente** basado en URL/subdominio
- **Base de datos compartida** (Cloud SQL)
- **Costos optimizados** al usar una sola instancia

## 📡 URLs de Acceso

### Aplicación Completa (Administración)
- `https://florezcook.appspot.com`
- `https://admin.florezcook.appspot.com`

### Portal de Clientes
- `https://cliente.florezcook.appspot.com`
- `https://portal.florezcook.appspot.com`
- `https://florezcook.appspot.com/cliente`

## 🛠️ Proceso de Despliegue

### Método 1: Script Automatizado (Recomendado)
```bash
# Desde el directorio raíz del proyecto
./deploy-unified.sh
```

### Método 2: Manual
```bash
# 1. Configurar proyecto
gcloud config set project appsindunnova

# 2. Desplegar aplicación
gcloud app deploy app.yaml --promote

# 3. Desplegar reglas de routing
gcloud app deploy dispatch.yaml

# 4. Verificar
curl https://florezcook.appspot.com/health
```

## 🏗️ Arquitectura Técnica

### Routing Inteligente
El archivo `main.py` detecta automáticamente qué interfaz mostrar:

```python
# Detección por subdominio
if 'cliente' in host or 'portal' in host:
    # Mostrar portal de clientes
    
# Detección por ruta
if path.startswith('/cliente'):
    # Mostrar portal de clientes
```

### Archivos Clave
- `main.py`: Aplicación principal unificada
- `app.yaml`: Configuración de App Engine
- `dispatch.yaml`: Reglas de routing de subdominios
- `deploy-unified.sh`: Script de despliegue automatizado

## 🔧 Configuración de Subdominios

### En Google Cloud Console:
1. Ve a **App Engine > Settings > Custom Domains**
2. Agrega dominios personalizados:
   - `cliente.tudominio.com` → default service
   - `portal.tudominio.com` → default service
   - `admin.tudominio.com` → default service

## 📊 Monitoreo y Logs

### Ver logs en tiempo real:
```bash
gcloud app logs tail -s default
```

### Métricas y performance:
- https://console.cloud.google.com/appengine
- https://console.cloud.google.com/monitoring

## 🚨 Troubleshooting

### Error: "Module not found"
```bash
# Verificar dependencias
pip install -r requirements.txt
```

### Error: "Cloud SQL connection"
```bash
# Verificar instancia de Cloud SQL
gcloud sql instances describe florezcook-instance
```

### Error: "Service account permissions"
```bash
# Verificar permisos
gcloud projects get-iam-policy appsindunnova
```

## 🔄 Actualizaciones

### Desplegar solo cambios de código:
```bash
gcloud app deploy app.yaml --no-promote
# Luego promover si todo está bien:
gcloud app services set-traffic default --splits=NUEVA_VERSION=100
```

### Rollback a versión anterior:
```bash
gcloud app versions list
gcloud app services set-traffic default --splits=VERSION_ANTERIOR=100
```

## 💰 Costos Estimados

### Con 1 servicio unificado:
- **Instancia F2**: ~$45-90/mes (dependiendo del tráfico)
- **Cloud SQL**: ~$25-50/mes
- **Total estimado**: $70-140/mes

### Ventajas vs 2 servicios separados:
- **Ahorro**: ~30-50% en costos de cómputo
- **Simplicidad**: Un solo punto de despliegue
- **Eficiencia**: Recursos compartidos

## 🔐 Seguridad

### HTTPS obligatorio:
- Todas las rutas usan `secure: always`
- Certificados SSL automáticos de Google

### Variables de entorno:
- Credenciales en variables de entorno
- Conexión segura a Cloud SQL

## 🎯 Próximos Pasos

1. **Ejecutar el despliegue**:
   ```bash
   ./deploy-unified.sh
   ```

2. **Verificar funcionamiento**:
   - Probar ambas interfaces
   - Verificar conexión a BD
   - Probar funcionalidades clave

3. **Configurar dominios personalizados** (opcional):
   - cliente.florezcook.com
   - admin.florezcook.com

4. **Configurar monitoreo**:
   - Alertas en Cloud Monitoring
   - Logs estructurados

## 📞 Soporte

Si tienes problemas durante el despliegue:

1. Revisa los logs: `gcloud app logs tail`
2. Verifica la configuración: `gcloud app describe`
3. Consulta el troubleshooting arriba

---

**¿Listo para desplegar?** Ejecuta: `./deploy-unified.sh`