.PHONY: help install dev test lint format typecheck build clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd api && poetry install
	cd worker && poetry install
	cd web && npm install --legacy-peer-deps

dev: ## Start the dev environment (docker-compose)
	docker-compose up -d db redis
	@echo "Starting API on :8000, Web on :3000"
	cd api && poetry run uvicorn main:app --reload &
	cd web && npm run dev

test: ## Run all tests
	cd api && poetry run pytest ../tests/ -v

test-backend: ## Run backend tests with coverage
	cd api && poetry run pytest ../tests/ -v --cov=verxlite_api --cov-report=term-missing

lint: ## Run linters
	cd api && poetry run ruff check .
	cd api && poetry run black --check .
	cd web && npm run lint

format: ## Run formatters
	cd api && poetry run ruff check --fix .
	cd api && poetry run black .
	cd web && npx prettier --write .

typecheck: ## Run type checkers
	cd api && poetry run mypy verxlite_api --ignore-missing-imports
	cd web && npx tsc --noEmit

build: ## Build Docker images
	docker-compose build

migrate: ## Run database migrations
	cd api && poetry run alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new name="add foo")
	cd api && poetry run alembic revision --autogenerate -m "$(name)"

init-db: ## Initialize the database with seed data
	cd api && poetry run python ../scripts/init_db.py

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf web/.next web/node_modules
	rm -rf api/.venv
	rm -f *.db
