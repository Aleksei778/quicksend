include .env

SHELL = /bin/sh
UID := $(shell id -u)
COMPOSE = docker compose -f docker-compose.local.yaml -p quicksend
NETWORK = ${DOCKER_NETWORK}

.PHONY: docker-network docker-up docker-down docker-restart docker-stop \
        app-bash db-bash db-console redis-bash redis-cli \
        uv-sync uv-add uv-add-dev uv-remove uv-lock \
        app-setup project-installation \
        db-migrate db-migrate-create db-rollback db-reset db-seed \
        alembic-upgrade alembic-downgrade alembic-revision alembic-current \
        test test-cov lint format \
        logs logs-app containers-status \
        help

# === DOCKER OPERATIONS ===
docker-network:
	@env UID=${UID} docker network create --driver bridge --subnet=172.70.0.0/16 --gateway=172.70.0.1 ${NETWORK} || true

docker-up:
	@env UID=${UID} $(COMPOSE) up -d --remove-orphans

docker-down:
	@env UID=${UID} $(COMPOSE) down

docker-restart: docker-down docker-up

docker-stop:
	@env UID=${UID} $(COMPOSE) stop

docker-clean:
	@env UID=${UID} $(COMPOSE) down -v --remove-orphans

# === CONTAINER ACCESS ===
app-bash:
	@env UID=${UID} $(COMPOSE) exec app bash

db-bash:
	@env UID=${UID} $(COMPOSE) exec db bash

# usage: make db-console
db-console:
	@env UID=${UID} $(COMPOSE) exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

redis-bash:
	@env UID=${UID} $(COMPOSE) exec redis bash

redis-cli:
	@env UID=${UID} $(COMPOSE) exec redis redis-cli

# === UV PACKAGE MANAGEMENT ===
uv-sync:
	@env UID=${UID} $(COMPOSE) exec app uv sync

uv-lock:
	@env UID=${UID} $(COMPOSE) exec app uv lock

# usage: make uv-add package=fastapi
uv-add:
	@env UID=${UID} $(COMPOSE) exec app uv add $(package)

# usage: make uv-add-dev package=pytest
uv-add-dev:
	@env UID=${UID} $(COMPOSE) exec app uv add --dev $(package)

# usage: make uv-remove package=fastapi
uv-remove:
	@env UID=${UID} $(COMPOSE) exec app uv remove $(package)

# === PROJECT SETUP ===
app-setup:
	@env UID=${UID} $(COMPOSE) exec app uv sync
	@echo "Python dependencies installed successfully"

project-installation: docker-up app-setup db-migrate
	@echo "Python project was successfully installed."

# === DATABASE MIGRATIONS (Alembic) ===
db-migrate:
	@env UID=${UID} $(COMPOSE) exec app alembic upgrade head

# usage: make db-migrate-create message="create users table"
db-migrate-create:
	@env UID=${UID} $(COMPOSE) exec app alembic revision --autogenerate -m "$(message)"

# usage: make db-rollback steps=1
db-rollback:
	@env UID=${UID} $(COMPOSE) exec app alembic downgrade -$(steps)

db-reset:
	@env UID=${UID} $(COMPOSE) exec app alembic downgrade base

alembic-upgrade:
	@env UID=${UID} $(COMPOSE) exec app alembic upgrade head

# usage: make alembic-downgrade revision=abc123
alembic-downgrade:
	@env UID=${UID} $(COMPOSE) exec app alembic downgrade $(revision)

# usage: make alembic-revision message="add user table"
alembic-revision:
	@env UID=${UID} $(COMPOSE) exec app alembic revision --autogenerate -m "$(message)"

alembic-current:
	@env UID=${UID} $(COMPOSE) exec app alembic current

# === DATABASE SEEDING ===
# usage: make db-seed
db-seed:
	@env UID=${UID} $(COMPOSE) exec app python -m app.seeds.run

# === TESTING ===
test:
	@env UID=${UID} $(COMPOSE) exec app pytest

test-cov:
	@env UID=${UID} $(COMPOSE) exec app pytest --cov=app --cov-report=html

test-watch:
	@env UID=${UID} $(COMPOSE) exec app pytest-watch

# === CODE QUALITY ===
lint:
	@env UID=${UID} $(COMPOSE) exec app ruff check .

format:
	@env UID=${UID} $(COMPOSE) exec app ruff format .

type-check:
	@env UID=${UID} $(COMPOSE) exec app mypy app

# === LOGS ===
logs:
	@env UID=${UID} docker compose -f docker-compose.local.yaml logs -f

logs-app:
	@env UID=${UID} docker compose -f docker-compose.local.yaml logs -f app

logs-db:
	@env UID=${UID} docker compose -f docker-compose.local.yaml logs -f db

# === STATUS ===
containers-status:
	@env UID=${UID} docker compose -f docker-compose.local.yaml ps

# === CELERY (if using) ===
celery-worker:
	@env UID=${UID} $(COMPOSE) exec app celery -A app.celery_app worker --loglevel=info

celery-beat:
	@env UID=${UID} $(COMPOSE) exec app celery -A app.celery_app beat --loglevel=info

celery-flower:
	@env UID=${UID} $(COMPOSE) exec app celery -A app.celery_app flower

# === HELP ===
help:
	@echo "Makefile Commands:"
	@echo ""
	@echo "  🚀 Docker Operations:"
	@echo "    docker-up          - Start Docker containers"
	@echo "    docker-down        - Stop and remove Docker containers"
	@echo "    docker-restart     - Restart Docker containers"
	@echo "    docker-stop        - Stop Docker containers"
	@echo "    docker-clean       - Remove containers and volumes"
	@echo ""
	@echo "  🐳 Container Access:"
	@echo "    app-bash           - Access Python app container bash"
	@echo "    db-bash            - Access database container bash"
	@echo "    db-console         - Access PostgreSQL console"
	@echo "    redis-bash         - Access Redis container bash"
	@echo "    redis-cli          - Access Redis CLI"
	@echo ""
	@echo "  📦 UV Package Management:"
	@echo "    uv-sync            - Sync dependencies from pyproject.toml"
	@echo "    uv-lock            - Update uv.lock file"
	@echo "    uv-add             - Add a package (usage: make uv-add package=fastapi)"
	@echo "    uv-add-dev         - Add a dev package (usage: make uv-add-dev package=pytest)"
	@echo "    uv-remove          - Remove a package (usage: make uv-remove package=fastapi)"
	@echo ""
	@echo "  🗄️ Database (Alembic):"
	@echo "    db-migrate         - Run all migrations"
	@echo "    db-migrate-create  - Create new migration (usage: make db-migrate-create message='text')"
	@echo "    db-rollback        - Rollback migrations (usage: make db-rollback steps=1)"
	@echo "    db-reset           - Reset all migrations"
	@echo "    db-seed            - Run database seeders"
	@echo "    alembic-current    - Show current migration"
	@echo ""
	@echo "  🧪 Testing:"
	@echo "    test               - Run tests"
	@echo "    test-cov           - Run tests with coverage"
	@echo "    test-watch         - Run tests in watch mode"
	@echo ""
	@echo "  ✨ Code Quality:"
	@echo "    lint               - Run ruff linter"
	@echo "    format             - Format code with ruff"
	@echo "    type-check         - Run mypy type checker"
	@echo ""
	@echo "  📊 Celery:"
	@echo "    celery-worker      - Start Celery worker"
	@echo "    celery-beat        - Start Celery beat scheduler"
	@echo "    celery-flower      - Start Flower monitoring"
	@echo ""
	@echo "  📝 Logs & Status:"
	@echo "    logs               - Show all container logs"
	@echo "    logs-app           - Show app container logs"
	@echo "    containers-status  - Show containers status"
