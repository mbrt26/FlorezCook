# Guía de Migración MySQL → PostgreSQL para FlorezCook

## Beneficios de PostgreSQL sobre MySQL en Google Cloud

1. **Costo**: ~30% más barato en Cloud SQL
2. **Rendimiento**: Mejor para consultas complejas
3. **Características**: JSON nativo, búsqueda full-text mejorada
4. **Licencia**: Totalmente open source

## Cambios Necesarios en el Código

### 1. Dependencias (requirements.txt)
```txt
# Remover
pymysql>=1.0.0

# Agregar
psycopg2-binary>=2.9.0
```

### 2. Configuración de Base de Datos (config/database.py)

```python
# Cambiar la URL de conexión
if os.getenv('ENV') == 'production':
    # PostgreSQL en Cloud SQL
    return create_engine(
        f'postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}'
        f'?host=/cloudsql/{connection_name}',
        pool_size=3,
        max_overflow=5,
        pool_timeout=20,
        pool_recycle=1800
    )
else:
    # PostgreSQL local
    return create_engine(
        f'postgresql://{db_user}:{db_pass}@localhost/{db_name}',
        echo=False
    )
```

### 3. Cambios en Modelos (models.py)

PostgreSQL es mayormente compatible, pero algunos ajustes menores:

```python
# MySQL
fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

# PostgreSQL (más eficiente)
fecha_creacion = Column(DateTime, server_default=func.now())
```

### 4. Migración de Datos

```bash
# 1. Exportar desde MySQL
mysqldump -h [HOST] -u [USER] -p[PASS] florezcook_db > backup.sql

# 2. Convertir SQL (usar herramienta)
# Recomendado: https://github.com/maxlapshin/mysql2postgres

# 3. Importar a PostgreSQL
psql -h [HOST] -U [USER] -d florezcook_db < converted.sql
```

## Configuración de Cloud SQL PostgreSQL

### 1. Crear instancia PostgreSQL
```bash
gcloud sql instances create florezcook-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \  # Instancia más barata
  --region=southamerica-east1 \
  --network=default \
  --no-backup \  # Sin backups automáticos (ahorra costos)
  --maintenance-window-day=SUN \
  --maintenance-window-hour=05
```

### 2. Crear base de datos
```bash
gcloud sql databases create florezcook_db \
  --instance=florezcook-postgres
```

### 3. Actualizar app.yaml
```yaml
env_variables:
  CLOUD_SQL_CONNECTION_NAME: appsindunnova:southamerica-east1:florezcook-postgres
  DB_TYPE: postgresql  # Agregar para diferenciar
```

## Optimizaciones Adicionales para Reducir Costos

### 1. Cache Agresivo
- Implementar Redis Memorystore para cache (~$25/mes)
- O usar Memcache gratuito de App Engine

### 2. CDN para Archivos Estáticos
- Usar Cloud CDN o Cloudflare (gratis)
- Reduce carga en App Engine

### 3. Cron Jobs Optimizados
```yaml
# cron.yaml
cron:
- description: "cleanup old sessions"
  url: /admin/cleanup
  schedule: every sunday 03:00
  target: florezcook
```

### 4. Compresión de Respuestas
```python
# En app.py
from flask_compress import Compress
Compress(app)  # Reduce ancho de banda
```

## Estimación de Ahorro Total

| Componente | Costo Actual | Costo Nuevo | Ahorro |
|------------|--------------|-------------|---------|
| App Engine F2 | $86/mes | $10-20/mes | ~$70/mes |
| Cloud SQL MySQL | $80/mes | $50/mes (PostgreSQL) | ~$30/mes |
| **Total** | **$166/mes** | **$60-70/mes** | **~$100/mes** |

## Pasos de Implementación

1. **Fase 1**: Cambiar a F1 (inmediato)
   - Aplicar app-f1.yaml
   - Monitorear rendimiento

2. **Fase 2**: Migrar a PostgreSQL (1-2 semanas)
   - Configurar instancia PostgreSQL
   - Migrar datos
   - Actualizar código
   - Probar exhaustivamente

3. **Fase 3**: Optimizaciones adicionales
   - Implementar cache
   - Configurar CDN
   - Ajustar queries