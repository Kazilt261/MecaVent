.DEFAULT_GOAL := help

.PHONY: help init dev ssh-back ssh-front makemigrations-dev migrate-dev reset-dev rebuild-dev logs down stats

help: ## Show this help with available commands
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Start services and run initial migrations
	docker compose up back-dev front-dev -d
	docker compose exec back-dev uv run manage.py makemigrations
	docker compose exec back-dev uv run manage.py migrate

dev: ## Start backend and frontend in detached mode
	docker compose up back-dev front-dev -d

ssh-back: ## Open a shell in the backend container
	docker compose exec back-dev /bin/bash

ssh-front: ## Open a shell in the frontend container
	docker compose exec front-dev /bin/bash

makemigrations-dev: ## Create new backend migrations
	docker compose exec back-dev uv run manage.py makemigrations

migrate-dev: ## Apply backend migrations
	docker compose exec back-dev uv run manage.py migrate

reset-dev: ## Reset dev environment removing volumes
	docker compose down -v
	docker compose up back-dev -d

rebuild-dev: ## Rebuild and start backend
	docker compose up back-dev -d --build

logs: ## Follow backend and frontend logs
	docker compose logs -f back-dev front-dev

down: ## Stop containers
	docker compose down

stats: ## Show container resource usage
	docker compose stats

prod: ## Build and start production containers
	docker compose up prod -d --build

logs-prod: ## Follow production backend and frontend logs
	docker compose logs -f prod

migrate-prod: ## Apply backend migrations in production
	docker compose exec prod uv run manage.py migrate

ssh-prod: ## Open a shell in the production backend container
	docker compose exec prod /bin/bash