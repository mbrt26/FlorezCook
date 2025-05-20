# Guía de Despliegue - FlorezCook

Esta guía proporciona instrucciones para desplegar la aplicación FlorezCook en Google Cloud Platform (GCP).

## Requisitos Previos

1. Cuenta de Google Cloud Platform con facturación habilitada
2. Google Cloud SDK instalado y configurado
3. Python 3.9 o superior instalado
4. Acceso a una instancia de Cloud SQL (MySQL 8.0)

## Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone [URL_DEL_REPOSITORIO]
cd FlorezCook
```

### 2. Configurar Variables de Entorno

1. Copiar el archivo `.env.example` a `.env`
2. Actualizar las variables en `.env` con tus credenciales

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

## Despliegue en Google Cloud Platform

### 1. Configurar el Proyecto de Google Cloud

```bash
gcloud config set project florezcook
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

### 2. Habilitar APIs Necesarias

```bash
gcloud services enable sqladmin.googleapis.com
```

### 3. Configurar Cloud SQL

Asegúrate de que la instancia de Cloud SQL esté configurada correctamente:

```bash
gcloud sql instances describe florezcook-db
```

### 4. Desplegar la Aplicación

```bash
gcloud app deploy
```

### 5. Inicializar la Base de Datos

Después del despliegue, inicializa la base de datos:

```bash
gcloud app services update default --update-env-vars="ENV=production"
```

## Configuración de Dominio Personalizado (Opcional)

1. Ve a la consola de Google Cloud
2. Navega a "App Engine" > "Configuración" > "Dominios personalizados"
3. Sigue las instrucciones para verificar tu dominio

## Monitoreo y Registros

Puedes ver los registros de la aplicación con:

```bash
gcloud app logs tail -s default
```

## Solución de Problemas

### Error de Conexión a la Base de Datos

1. Verifica que la instancia de Cloud SQL esté en ejecución
2. Asegúrate de que la dirección IP de App Engine esté en la lista blanca
3. Verifica que el usuario y la contraseña sean correctos

### La Aplicación no se Inicia

1. Revisa los registros de la aplicación
2. Verifica que todas las variables de entorno estén configuradas correctamente
3. Asegúrate de que el puerto 8080 esté abierto

## Mantenimiento

### Actualizar la Aplicación

1. Realiza los cambios en el código
2. Prueba localmente
3. Despliega los cambios:

```bash
gcloud app deploy
```

### Escalar la Aplicación

Puedes ajustar los recursos en el archivo `app.yaml` bajo la sección `resources`.

## Seguridad

- No expongas credenciales en el código fuente
- Utiliza Secret Manager para gestionar secretos en producción
- Mantén las dependencias actualizadas

## Soporte

Para problemas técnicos, por favor abre un issue en el repositorio del proyecto.
