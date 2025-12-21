include .env

SHELL = /bin/sh
UID := $(shell id -u)
EXEC = docker compose -p template exec

.PHONY: docker-up docker-down docker-restart docker-stop docker-clean \
        php-bash db-bash db-console node-bash redis-bash redis-cli \
        composer-install composer-update composer-require composer-require-d composer-remove \
        laravel-setup project-installation \
        db-migrate db-migrate-force db-reset db-rollback db-fresh db-fresh-seed db-make-migration db-seed db-seed-class \
        npm-install npm-dev npm-build npm-watch \
        logs logs-container logs-laravel containers-status \
        help

# === DOCKER OPERATIONS ===
docker-up:
	@env UID=${UID} docker compose -p template up -d --remove-orphans

docker-down:
	@env UID=${UID} docker compose -p template down

docker-restart: docker-down docker-up

docker-stop:
	@env UID=${UID} docker compose -p template stop

# === CONTAINER ACCESS ===
php-bash:
	@env UID=${UID} $(EXEC) php-unit bash

db-bash:
	@env UID=${UID} $(EXEC) db bash

# usage: make db-console username=YOUR_USERNAME
db-console:
	@env UID=${UID} $(EXEC) db psql -U $(user)

node-bash:
	@env UID=${UID} $(EXEC) node bash

redis-bash:
	@env UID=${UID} $(EXEC) redis bash

redis-cli:
	@env UID=${UID} $(EXEC) redis redis-cli

# === PROJECT INSTALLATION ===
composer-install:
	@env UID=${UID} $(EXEC) php-unit composer install --no-interaction --optimize-autoloader

composer-update:
	@env UID=${UID} $(EXEC) php-unit composer update --no-interaction --optimize-autoloader

# usage: make composer-require package=laravel/sanctum
composer-require:
	@env UID=${UID} $(EXEC) php-unit composer require $(package)

#usage: make composer-require-d package=laravel/sanctum
composer-require-d:
	@env UID=${UID} $(EXEC) php-unit composer require --dev $(package)

#usage: make composer-remove package=laravel/sanctum
composer-remove:
	@env UID=${UID} $(EXEC) php-unit composer remove $(package)

laravel-setup:
	@env UID=${UID} $(EXEC) php-unit php artisan key:generate
	@env UID=${UID} docker compose -p template restart php-unit

project-installation: docker-up composer-install laravel-setup db-migrate
	@echo "Laravel project was successfully installed."

# === MIGRATIONS ===
db-migrate:
	@env UID=${UID} $(EXEC) php-unit php artisan migrate

db-migrate-force:
	@env UID=${UID} $(EXEC) php-unit php artisan migrate --force

db-reset:
	@env UID=${UID} $(EXEC) php-unit php artisan migrate:reset

# usage: make db-rollback step=2
db-rollback:
	@env UID=${UID} $(EXEC) php-unit php artisan migrate:rollback --step=$(step)

db-fresh:
	@env UID=${UID} $(EXEC) php-unit php artisan migrate:fresh

db-fresh-seed:
	@env UID=${UID} $(EXEC) php-unit php artisan migrate:fresh --seed

# usage: make db-make-migration name=create_users_table
db-make-migration:
	@env UID=${UID} $(EXEC) php-unit php artisan make:migration $(name)

db-seed:
	@env UID=${UID} $(EXEC) php-unit php artisan db:seed

# usage: make db-seed-class class=AdminSeeder
db-seed-class:
	@env UID=${UID} $(EXEC) php-unit php artisan db:seed --class=$(class)

# === FRONTEND ===
npm-install:
	@env UID=${UID} $(EXEC) node npm install

npm-dev:
	@env UID=${UID} $(EXEC) node npm run dev

npm-build:
	@env UID=${UID} $(EXEC) node npm run build

# === HELP ===
help:
	@echo "Makefile Commands:"
	@echo ""
	@echo "  🚀 Docker Operations:"
	@echo "    docker-up          - Start Docker containers"
	@echo "    docker-down        - Stop and remove Docker containers"
	@echo "    docker-restart     - Restart Docker containers"
	@echo "    docker-stop        - Stop Docker containers"
	@echo ""
	@echo "  🐳 Container Access:"
	@echo "    php-bash           - Access PHP container bash"
	@echo "    db-bash            - Access database container bash"
	@echo "    db-console         - Access PostgreSQL console"
	@echo "    node-bash          - Access Node container bash"
	@echo "    redis-bash         - Access Redis container bash"
	@echo "    redis-cli          - Access Redis CLI"
	@echo ""
	@echo "  📦 Composer:"
	@echo "    composer-install   - Install PHP dependencies"
	@echo "    composer-update    - Update PHP dependencies"
	@echo "    composer-require   - Add a package (usage: make composer-require package=name)"
	@echo "    composer-require-d - Add a dev package (usage: make composer-require-dev package=name)"
	@echo "    composer-remove    - Remove a package (usage: make composer-remove package=name)"
	@echo ""
	@echo "  🗄️ Database:"
	@echo "    db-migrate         - Run database migrations"
	@echo "    db-migrate-force   - Force run database migrations"
	@echo "    db-reset           - Reset all migrations"
	@echo "    db-rollback        - Rollback migrations (usage: make db-rollback step=N)"
	@echo "    db-fresh           - Drop and recreate database with migrations"
	@echo "    db-fresh-seed      - Drop, recreate, and seed database"
	@echo "    db-make-migration  - Create a new migration (usage: make db-make-migration name=name)"
	@echo "    db-seed            - Run all database seeders"
	@echo "    db-seed-class      - Run a specific seeder (usage: make db-seed-class class=name)"
	@echo ""
	@echo "  🎯 Frontend:"
	@echo "    npm-install        - Install Node dependencies"
	@echo "    npm-dev            - Run main development build"
	@echo "    npm-build          - Run main production build"
