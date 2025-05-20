# [START makefile]
# Makefile para el proyecto FlorezCook
# Comandos útiles para desarrollo y despliegue

# Variables
PROJECT_ID := florezcook
REGION := us-central1
SERVICE_ACCOUNT_EMAIL := $(shell gcloud config get-value account)

# Colores
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

.PHONY: help
## Muestra esta ayuda
help:
	@echo "\n${YELLOW}Uso:${RESET}\n  make ${GREEN}<comando>${RESET}\n\n${YELLOW}Comandos:${RESET}"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${GREEN}%-30s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ===== Configuración del proyecto =====

.PHONY: setup
## Configura el entorno de desarrollo
setup: venv
	@echo "${YELLOW}Instalando dependencias...${RESET}"
	. venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt
	@echo "${GREEN}✓ Entorno configurado correctamente${RESET}"

.PHONY: venv
## Crea un entorno virtual de Python
venv:
	@if [ ! -d "venv" ]; then \
		echo "${YELLOW}Creando entorno virtual...${RESET}"; \
		python3 -m venv venv; \
	fi

# ===== Desarrollo =====

.PHONY: run
## Inicia el servidor de desarrollo
run: venv
	@echo "${YELLOW}Iniciando servidor de desarrollo...${RESET}"
	. venv/bin/activate && FLASK_APP=main.py FLASK_DEBUG=1 flask run --port=8080

.PHONY: test
## Ejecuta las pruebas
TEST_PATH=./tests
test: venv
	@echo "${YELLOW}Ejecutando pruebas...${RESET}"
	. venv/bin/activate && python -m pytest -v $(TEST_PATH)

.PHONY: lint
## Ejecuta el linter
lint: venv
	@echo "${YELLOW}Ejecutando linter...${RESET}"
	. venv/bin/activate && flake8 app tests
	. venv/bin/activate && black --check app tests
	. venv/bin/activate && isort --check-only app tests

.PHONY: format
## Formatea el código
format: venv
	@echo "${YELLOW}Formateando código...${RESET}"
	. venv/bin/activate && black app tests
	. venv/bin/activate && isort app tests

# ===== Docker =====

.PHONY: docker-build
## Construye la imagen de Docker
docker-build:
	@echo "${YELLOW}Construyendo imagen de Docker...${RESET}"
	docker-compose build

.PHONY: docker-up
## Inicia los contenedores de Docker
docker-up:
	@echo "${YELLOW}Iniciando contenedores...${RESET}"
	docker-compose up -d

.PHONY: docker-down
## Detiene los contenedores de Docker
docker-down:
	@echo "${YELLOW}Deteniendo contenedores...${RESET}"
	docker-compose down

.PHONY: docker-logs
## Muestra los logs de los contenedores
docker-logs:
	docker-compose logs -f

# ===== Despliegue =====

.PHONY: deploy
## Despliega la aplicación en Google Cloud
deploy:
	@echo "${YELLOW}Desplegando en Google Cloud...${RESET}"
	./deploy.sh

.PHONY: gcloud-auth
## Autentica en Google Cloud
gcloud-auth:
	@echo "${YELLOW}Autenticando en Google Cloud...${RESET}"
	gcloud auth login
	gcloud config set project $(PROJECT_ID)
	gcloud auth application-default login

.PHONY: gcloud-configure
## Configura el proyecto de Google Cloud
gcloud-configure:
	@echo "${YELLOW}Configurando proyecto de Google Cloud...${RESET}"
	gcloud config set project $(PROJECT_ID)
	gcloud config set compute/region $(REGION)
	gcloud config set run/region $(REGION)

# ===== Utilidades =====

.PHONY: clean
## Limpia archivos generados
clean:
	@echo "${YELLOW}Limpiando archivos generados...${RESET}"
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	rm -rf .coverage htmlcov/

.PHONY: reset-db
## Reinicia la base de datos (solo desarrollo)
reset-db:
	@echo "${YELLOW}Reiniciando base de datos...${RESET}"
	docker-compose down -v
	docker-compose up -d db
	@echo "${YELLOW}Esperando a que la base de datos esté lista...${RESET}"
	@until docker-compose exec -T db mysql -u root -p"$$(grep DB_PASSWORD .env | cut -d '=' -f2)" -e "SELECT 1" > /dev/null 2>&1; do \
		sleep 5; \
		echo "${YELLOW}Esperando a que la base de datos esté lista...${RESET}"; \
	done
	@echo "${GREEN}✓ Base de datos lista${RESET}"

.PHONY: shell
## Abre una shell en el contenedor de la aplicación
shell:
	docker-compose exec app sh

# [END makefile]
