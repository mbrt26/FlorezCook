#!/bin/bash
# Script de gestión Docker para FlorezCook
# Versión: 2025.06.24

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}🐳 FlorezCook Docker Manager${NC}"
    echo ""
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "COMANDOS DISPONIBLES:"
    echo "  build       - Construir todas las imágenes Docker"
    echo "  up          - Levantar todos los servicios"
    echo "  down        - Detener todos los servicios"
    echo "  restart     - Reiniciar todos los servicios"
    echo "  logs        - Mostrar logs de todos los servicios"
    echo "  logs-admin  - Mostrar logs solo del admin"
    echo "  logs-client - Mostrar logs solo del cliente"
    echo "  logs-db     - Mostrar logs de la base de datos"
    echo "  status      - Mostrar estado de los contenedores"
    echo "  clean       - Limpiar contenedores e imágenes no utilizadas"
    echo "  reset       - Resetear completamente (CUIDADO: borra datos)"
    echo "  shell-admin - Acceder al shell del contenedor admin"
    echo "  shell-client- Acceder al shell del contenedor cliente"
    echo "  shell-db    - Acceder al shell de MySQL"
    echo "  backup-db   - Crear backup de la base de datos"
    echo "  restore-db  - Restaurar backup de la base de datos"
    echo "  help        - Mostrar esta ayuda"
    echo ""
}

# Función para verificar que Docker está corriendo
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker no está corriendo. Por favor, inicia Docker Desktop.${NC}"
        exit 1
    fi
}

# Función para verificar que docker-compose existe
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}⚠️  docker-compose no encontrado, intentando con 'docker compose'${NC}"
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
}

# Función para crear el archivo .env si no existe
setup_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}📝 Creando archivo .env desde .env.docker...${NC}"
        cp .env.docker .env
        echo -e "${GREEN}✅ Archivo .env creado. Puedes editarlo según tus necesidades.${NC}"
    fi
}

# Construir imágenes
build_images() {
    echo -e "${BLUE}🔨 Construyendo imágenes Docker...${NC}"
    $DOCKER_COMPOSE build --no-cache
    echo -e "${GREEN}✅ Imágenes construidas exitosamente${NC}"
}

# Levantar servicios
start_services() {
    echo -e "${BLUE}🚀 Levantando servicios FlorezCook...${NC}"
    $DOCKER_COMPOSE up -d
    echo ""
    echo -e "${GREEN}✅ Servicios iniciados exitosamente${NC}"
    echo ""
    echo -e "${YELLOW}📱 Accesos disponibles:${NC}"
    echo "  🌐 Aplicación Principal (Admin): http://localhost:80"
    echo "  👥 Portal de Clientes: http://localhost:80/cliente"  
    echo "  🔍 Health Check Admin: http://localhost:8080/health"
    echo "  🔍 Health Check Cliente: http://localhost:8081/health"
    echo "  🗄️  Base de Datos MySQL: localhost:3306"
    echo ""
}

# Detener servicios
stop_services() {
    echo -e "${BLUE}🛑 Deteniendo servicios...${NC}"
    $DOCKER_COMPOSE down
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
}

# Reiniciar servicios
restart_services() {
    echo -e "${BLUE}🔄 Reiniciando servicios...${NC}"
    $DOCKER_COMPOSE restart
    echo -e "${GREEN}✅ Servicios reiniciados${NC}"
}

# Mostrar logs
show_logs() {
    case $1 in
        "admin")
            echo -e "${BLUE}📋 Logs del Admin...${NC}"
            $DOCKER_COMPOSE logs -f app-admin
            ;;
        "client")
            echo -e "${BLUE}📋 Logs del Cliente...${NC}"
            $DOCKER_COMPOSE logs -f app-cliente
            ;;
        "db")
            echo -e "${BLUE}📋 Logs de la Base de Datos...${NC}"
            $DOCKER_COMPOSE logs -f database
            ;;
        *)
            echo -e "${BLUE}📋 Logs de todos los servicios...${NC}"
            $DOCKER_COMPOSE logs -f
            ;;
    esac
}

# Mostrar estado
show_status() {
    echo -e "${BLUE}📊 Estado de los contenedores FlorezCook:${NC}"
    $DOCKER_COMPOSE ps
    echo ""
    echo -e "${BLUE}💾 Uso de volúmenes:${NC}"
    docker volume ls | grep florezcook || echo "No hay volúmenes de FlorezCook"
}

# Limpiar recursos no utilizados
clean_resources() {
    echo -e "${YELLOW}🧹 Limpiando recursos Docker no utilizados...${NC}"
    docker system prune -f
    echo -e "${GREEN}✅ Limpieza completada${NC}"
}

# Reset completo (PELIGROSO)
reset_all() {
    echo -e "${RED}⚠️  CUIDADO: Esto eliminará TODOS los datos de FlorezCook${NC}"
    read -p "¿Estás seguro? Escribe 'RESET' para confirmar: " confirm
    if [ "$confirm" = "RESET" ]; then
        echo -e "${YELLOW}🗑️  Eliminando todo...${NC}"
        $DOCKER_COMPOSE down -v --remove-orphans
        docker system prune -af
        docker volume rm florezcook-mysql-data 2>/dev/null || true
        echo -e "${GREEN}✅ Reset completo realizado${NC}"
    else
        echo -e "${BLUE}❌ Reset cancelado${NC}"
    fi
}

# Acceder al shell
access_shell() {
    case $1 in
        "admin")
            echo -e "${BLUE}🖥️  Accediendo al shell del Admin...${NC}"
            $DOCKER_COMPOSE exec app-admin /bin/bash
            ;;
        "client")
            echo -e "${BLUE}🖥️  Accediendo al shell del Cliente...${NC}"
            $DOCKER_COMPOSE exec app-cliente /bin/bash
            ;;
        "db")
            echo -e "${BLUE}🗄️  Accediendo a MySQL...${NC}"
            $DOCKER_COMPOSE exec database mysql -u florezcook_user -p florezcook
            ;;
    esac
}

# Backup de base de datos
backup_database() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${BLUE}💾 Creando backup de la base de datos...${NC}"
    $DOCKER_COMPOSE exec database mysqldump -u florezcook_user -pflorezcook_pass_2025_secure florezcook > $BACKUP_FILE
    echo -e "${GREEN}✅ Backup creado: $BACKUP_FILE${NC}"
}

# Restaurar base de datos
restore_database() {
    echo -e "${YELLOW}📂 Archivos de backup disponibles:${NC}"
    ls -la backup_*.sql 2>/dev/null || echo "No hay backups disponibles"
    echo ""
    read -p "Ingresa el nombre del archivo de backup: " backup_file
    if [ -f "$backup_file" ]; then
        echo -e "${BLUE}📥 Restaurando backup...${NC}"
        $DOCKER_COMPOSE exec -T database mysql -u florezcook_user -pflorezcook_pass_2025_secure florezcook < $backup_file
        echo -e "${GREEN}✅ Backup restaurado exitosamente${NC}"
    else
        echo -e "${RED}❌ Archivo de backup no encontrado${NC}"
    fi
}

# Función principal
main() {
    check_docker
    check_compose
    setup_env
    
    case $1 in
        "build")
            build_images
            ;;
        "up")
            start_services
            ;;
        "down")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            show_logs
            ;;
        "logs-admin")
            show_logs "admin"
            ;;
        "logs-client")
            show_logs "client"
            ;;
        "logs-db")
            show_logs "db"
            ;;
        "status")
            show_status
            ;;
        "clean")
            clean_resources
            ;;
        "reset")
            reset_all
            ;;
        "shell-admin")
            access_shell "admin"
            ;;
        "shell-client")
            access_shell "client"
            ;;
        "shell-db")
            access_shell "db"
            ;;
        "backup-db")
            backup_database
            ;;
        "restore-db")
            restore_database
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            echo -e "${RED}❌ Comando no reconocido: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal con todos los argumentos
main "$@"