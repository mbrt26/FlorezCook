# 🐳 FlorezCook Docker - Guía de Uso

## 📋 Resumen de la Dockerización

FlorezCook ahora está completamente dockerizado con una arquitectura de microservicios que incluye:

- **🌐 Aplicación Principal (Admin)**: Puerto 8080
- **👥 Portal de Clientes**: Puerto 8081  
- **🗄️ Base de Datos MySQL**: Puerto 3306
- **🔄 Proxy Nginx**: Puerto 80/443

## 🚀 Inicio Rápido

### 1. **Configuración Inicial**
```bash
# Copiar configuración de entorno
cp .env.docker .env

# (Opcional) Editar variables según tus necesidades
nano .env
```

### 2. **Levantar Servicios**
```bash
# Usando el script de gestión (RECOMENDADO)
./docker-manager.sh up

# O usando docker-compose directamente
docker-compose up -d
```

### 3. **Verificar Estado**
```bash
# Ver estado de contenedores
./docker-manager.sh status

# Ver logs en tiempo real
./docker-manager.sh logs
```

## 📱 Accesos Disponibles

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Admin Principal** | http://localhost | Sistema completo de gestión |
| **Portal Clientes** | http://localhost/cliente | Portal específico para clientes |
| **API Admin** | http://localhost:8080 | API directa del admin |
| **API Cliente** | http://localhost:8081 | API directa del cliente |
| **Base de Datos** | localhost:3306 | MySQL (usuario: florezcook_user) |

## 🛠️ Comandos Útiles

### **Gestión de Servicios**
```bash
./docker-manager.sh up          # Levantar servicios
./docker-manager.sh down        # Detener servicios
./docker-manager.sh restart     # Reiniciar servicios
./docker-manager.sh status      # Ver estado
```

### **Monitoreo y Logs**
```bash
./docker-manager.sh logs        # Logs de todos los servicios
./docker-manager.sh logs-admin  # Solo logs del admin
./docker-manager.sh logs-client # Solo logs del cliente
./docker-manager.sh logs-db     # Solo logs de la BD
```

### **Acceso a Contenedores**
```bash
./docker-manager.sh shell-admin   # Shell del contenedor admin
./docker-manager.sh shell-client  # Shell del contenedor cliente
./docker-manager.sh shell-db      # Acceso a MySQL
```

### **Gestión de Base de Datos**
```bash
./docker-manager.sh backup-db   # Crear backup
./docker-manager.sh restore-db  # Restaurar backup
```

### **Construcción y Limpieza**
```bash
./docker-manager.sh build       # Reconstruir imágenes
./docker-manager.sh clean       # Limpiar recursos no usados
./docker-manager.sh reset       # Reset completo (CUIDADO!)
```

## 🔧 Estructura de Archivos Docker

```
FlorezCook/
├── docker-compose.yml          # Orquestación principal
├── Dockerfile                  # Imagen del admin
├── Dockerfile.cliente         # Imagen del portal cliente
├── .dockerignore              # Archivos a ignorar
├── .env.docker               # Plantilla de configuración
├── .env                      # Configuración personalizada
├── docker-manager.sh         # Script de gestión
└── docker/
    ├── mysql/
    │   └── init.sql          # Inicialización de BD
    └── nginx/
        └── nginx.conf        # Configuración del proxy
```

## ⚡ Ventajas de Esta Dockerización

### **✅ Desarrollo Mejorado**
- Entorno idéntico en desarrollo y producción
- No más problemas de "funciona en mi máquina"
- Setup rápido para nuevos desarrolladores

### **✅ Aislamiento de Servicios**
- Admin y Cliente ejecutándose independientemente
- Sin conflictos de dependencias entre servicios
- Escalabilidad horizontal cuando sea necesario

### **✅ Gestión Simplificada**
- Un solo comando para levantar todo el stack
- Logs centralizados y organizados
- Backups automáticos de base de datos

### **✅ Migración Segura**
- Rollback instantáneo si algo falla
- Testing en contenedores antes del deploy
- Portabilidad entre providers (GCP, AWS, Azure)

## 🔒 Configuración de Seguridad

### **Variables de Entorno Importantes**
```bash
# Cambiar en producción
MYSQL_ROOT_PASSWORD=tu_password_super_seguro
MYSQL_PASSWORD=password_del_usuario_seguro
SECRET_KEY=clave_secreta_de_flask_muy_larga
```

### **Puertos Expuestos**
- **80**: Nginx (acceso principal)
- **8080**: Admin directo (opcional en producción)
- **8081**: Cliente directo (opcional en producción)
- **3306**: MySQL (solo para desarrollo)

## 🚨 Troubleshooting

### **Problema: Contenedores no inician**
```bash
# Verificar logs
./docker-manager.sh logs

# Verificar estado de Docker
docker info

# Verificar puertos en uso
lsof -i :80 -i :8080 -i :8081 -i :3306
```

### **Problema: Base de datos no conecta**
```bash
# Verificar health check de BD
docker-compose ps

# Acceder directamente a MySQL
./docker-manager.sh shell-db

# Recrear volumen de BD (CUIDADO: borra datos)
./docker-manager.sh reset
```

### **Problema: Aplicación da error 500**
```bash
# Ver logs específicos
./docker-manager.sh logs-admin
./docker-manager.sh logs-client

# Verificar variables de entorno
docker-compose config

# Reconstruir imágenes
./docker-manager.sh build
```

## 📈 Próximos Pasos

1. **SSL/HTTPS**: Configurar certificados SSL para producción
2. **CI/CD**: Integrar con GitHub Actions o GitLab CI
3. **Monitoring**: Añadir Prometheus + Grafana para métricas
4. **Scaling**: Configurar múltiples réplicas para alta disponibilidad

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs: `./docker-manager.sh logs`
2. Verifica la configuración: `docker-compose config`
3. Consulta esta documentación
4. Crea un issue en el repositorio

---

**¡FlorezCook está listo para producción con Docker! 🎉**