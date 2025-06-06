# FlorezCook - Sistema de Gestión de Restaurante

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema de gestión de restaurante desarrollado con Flask y desplegado en Google Cloud Platform.

## Características

- Gestión de menú y categorías
- Control de inventario
- Gestión de pedidos
- Reportes y análisis
- Panel de administración
- Autenticación de usuarios

## Requisitos Previos

- Python 3.9 o superior
- Google Cloud SDK instalado y configurado
- Una cuenta de Google Cloud Platform con facturación habilitada
- Una instancia de Cloud SQL (MySQL 8.0)
- Navegador web moderno

## Instalación Local

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tuusuario/florezcook.git
   cd florezcook
   ```

2. **Crear un entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   Copia el archivo `.env.example` a `.env` y configura las variables según tu entorno local.

5. **Inicializar la base de datos**
   ```bash
   python init_db.py
   ```

6. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

   La aplicación estará disponible en `http://localhost:8080`

## Despliegue en Google Cloud Platform

### Prerrequisitos

1. Tener instalado Google Cloud SDK
2. Tener una cuenta de Google Cloud Platform con facturación habilitada
3. Tener una instancia de Cloud SQL (MySQL 8.0) configurada

### Pasos para el despliegue

1. **Autenticación en Google Cloud**
   ```bash
   gcloud auth login
   gcloud config set project [TU_PROYECTO_ID]
   ```

2. **Configurar el proyecto**
   ```bash
   ./deploy.sh
   ```

   El script te guiará a través del proceso de despliegue.

3. **Acceder a la aplicación**
   Una vez finalizado el despliegue, podrás acceder a tu aplicación en:
   ```
   https://[TU_PROYECTO_ID].ue.r.appspot.com
   ```

## Configuración de la Base de Datos en Producción

1. **Crear una instancia de Cloud SQL**
   ```bash
   gcloud sql instances create florezcook-db \
       --database-version=MYSQL_8_0 \
       --tier=db-f1-micro \
       --region=us-central1 \
       --root-password=[TU_CONTRASEÑA_SEGURA]
   ```

2. **Crear una base de datos**
   ```bash
   gcloud sql databases create florezcook_db --instance=florezcook-db
   ```

3. **Configurar conexión**
   Asegúrate de que el archivo `.env` contenga las credenciales correctas:
   ```
   DB_USER=root
   DB_PASS=[TU_CONTRASEÑA_SEGURA]
   DB_NAME=florezcook_db
   CLOUD_SQL_CONNECTION_NAME=[TU_PROYECTO_ID]:us-central1:florezcook-db
   ```

## Estructura del Proyecto

```
florezcook/
├── app/                      # Código fuente de la aplicación
│   ├── __init__.py
│   ├── models.py             # Modelos de la base de datos
│   ├── routes.py             # Rutas de la aplicación
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes)
│   └── templates/            # Plantillas HTML
├── migrations/               # Migraciones de la base de datos
├── tests/                    # Pruebas unitarias
├── .env.example              # Ejemplo de variables de entorno
├── .gcloudignore             # Archivos a ignorar en el despliegue
├── app.yaml                  # Configuración de Google App Engine
├── cloudbuild.yaml           # Configuración de Cloud Build
├── deploy.sh                 # Script de despliegue
├── init_db.py                # Inicialización de la base de datos
├── main.py                   # Punto de entrada de la aplicación
└── requirements.txt          # Dependencias de Python
```

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```
# Configuración de la aplicación
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta_aqui

# Configuración de la base de datos local
DB_USER=root
DB_PASS=tu_contraseña
DB_NAME=florezcook_db
DB_HOST=localhost

# Configuración de Cloud SQL
CLOUD_SQL_CONNECTION_NAME=tu-proyecto:us-central1:florezcook-db
ENV=production

# Configuración de Google Cloud
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
```

## Solución de Problemas

### Error de conexión a la base de datos

Si la aplicación no puede conectarse a la base de datos, verifica:

1. Que la instancia de Cloud SQL esté en ejecución
2. Que la dirección IP de App Engine esté en la lista blanca de la base de datos
3. Que el nombre de usuario y contraseña sean correctos
4. Que el nombre de la base de datos exista

### La aplicación no se inicia

1. Revisa los logs de la aplicación:
   ```bash
   gcloud app logs tail -s default
   ```

2. Verifica que todas las variables de entorno estén configuradas correctamente
3. Asegúrate de que el puerto 8080 esté disponible

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Haz push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tucuenta](https://twitter.com/tucuenta) - email@ejemplo.com

Enlace del proyecto: [https://github.com/tuusuario/florezcook](https://github.com/tuusuario/florezcook)

## Agradecimientos

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Google Cloud Platform](https://cloud.google.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
