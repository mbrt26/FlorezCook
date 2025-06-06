# Guía de Despliegue - FlorezCook en apps-indunnova

## Resumen
Esta guía te ayudará a desplegar FlorezCook como un servicio separado en el proyecto "apps-indunnova" de Google Cloud Platform.

## Pre-requisitos

### 1. Instalación de Google Cloud SDK
```bash
# Para macOS
brew install --cask google-cloud-sdk

# O descarga desde: https://cloud.google.com/sdk/docs/install
```

### 2. Autenticación
```bash
gcloud auth login
gcloud config set project apps-indunnova
```

## Configuración de la Base de Datos

### 1. Crear instancia de Cloud SQL (si no existe)
```bash
# Crear instancia de MySQL en Cloud SQL
gcloud sql instances create florezcook-instance \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=southamerica-east1 \
    --project=appsindunnova

# Crear la base de datos
gcloud sql databases create florezcook_db \
    --instance=florezcook-instance \
    --project=appsindunnova

# Crear usuario específico para la aplicación
gcloud sql users create florezcook_user \
    --instance=florezcook-instance \
    --password=FlorezCook2025! \
    --project=appsindunnova
```

### 2. Actualizar configuración en app-indunnova.yaml
Antes del despliegue, actualiza estos valores en `app-indunnova.yaml`:

```yaml
env_variables:
  DB_USER: "florezcook_user"
  DB_PASS: "FlorezCook2025!"
  DB_NAME: "florezcook_db"
  CLOUD_SQL_CONNECTION_NAME: "appsindunnova:southamerica-east1:florezcook-instance"

beta_settings:
  cloud_sql_instances: "appsindunnova:southamerica-east1:florezcook-instance"
```

## Despliegue

### Opción 1: Script Automatizado (Recomendado)
```bash
./deploy-indunnova.sh
```

### Opción 2: Comando Manual
```bash
gcloud app deploy app-indunnova.yaml \
    --project=apps-indunnova \
    --version=v$(date +%Y%m%d-%H%M%S) \
    --promote
```

## Verificación del Despliegue

### 1. Verificar servicios activos
```bash
gcloud app services list --project=apps-indunnova
```

### 2. Ver logs en tiempo real
```bash
gcloud app logs tail -s florezcook --project=apps-indunnova
```

### 3. Acceder a la aplicación
- URL del servicio: `https://florezcook-dot-apps-indunnova.appspot.com`
- Panel de control: https://console.cloud.google.com/appengine/services?project=apps-indunnova

## Configuración de Seguridad

### Variables de entorno sensibles
Para mayor seguridad, considera usar Google Secret Manager:

```bash
# Crear secreto para la contraseña de la BD
gcloud secrets create db-password \
    --data-file=- \
    --project=apps-indunnova <<< "TuContraseñaSegura123!"

# Dar permisos al App Engine
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:apps-indunnova@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=apps-indunnova
```

## Solución de Problemas

### Error de conexión a la base de datos
1. Verificar que Cloud SQL esté activo
2. Revisar las credenciales en app-indunnova.yaml
3. Confirmar el nombre de la instancia Cloud SQL

### Error 502/503
1. Revisar los logs: `gcloud app logs tail -s florezcook`
2. Verificar que todas las dependencias estén en requirements.txt
3. Aumentar el timeout en app-indunnova.yaml

### Error de permisos
```bash
# Verificar permisos del proyecto
gcloud projects get-iam-policy apps-indunnova

# Agregar rol de App Engine Admin si es necesario
gcloud projects add-iam-policy-binding apps-indunnova \
    --member="user:tu-email@domain.com" \
    --role="roles/appengine.appAdmin"
```

## Comandos Útiles

```bash
# Ver todas las versiones
gcloud app versions list --service=florezcook --project=apps-indunnova

# Cambiar tráfico entre versiones
gcloud app services set-traffic florezcook --splits=VERSION_ID=100 --project=apps-indunnova

# Eliminar versiones antiguas
gcloud app versions delete VERSION_ID --service=florezcook --project=apps-indunnova

# Escalar el servicio
gcloud app services set-traffic florezcook --splits=VERSION_ID=100 --project=apps-indunnova
```

## Monitoreo y Mantenimiento

### Logs
- Logs de aplicación: Cloud Console > App Engine > Logs
- Métricas: Cloud Console > App Engine > Dashboard

### Backup de base de datos
```bash
# Backup automático (recomendado configurar en Cloud SQL)
gcloud sql backups create --instance=florezcook-instance --project=apps-indunnova
```

### Actualizaciones
Para actualizar la aplicación, simplemente ejecuta de nuevo el script de despliegue:
```bash
./deploy-indunnova.sh
```

## Contacto y Soporte
- Panel de App Engine: https://console.cloud.google.com/appengine
- Documentación: https://cloud.google.com/appengine/docs