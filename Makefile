.PHONY: help setup up down clean migrate seed test lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup - copy env file and create venv
	@if [ ! -f .env.local ]; then \
		cp .env.example .env.local; \
		echo "Created .env.local - please update with your values"; \
	else \
		echo ".env.local already exists"; \
	fi
	@if [ ! -d .venv ]; then \
		python -m venv .venv; \
		echo "Created virtual environment"; \
	fi

up: ## Start all services with docker-compose
	docker-compose up -d
	@echo "Services started. Check status with: docker-compose ps"

down: ## Stop all services
	docker-compose down

clean: ## Stop services and remove volumes
	docker-compose down -v
	@echo "All services stopped and volumes removed"

migrate: ## Run database migrations
	@echo "Running migrations..."
	@./ops/migrate.sh

seed-skills: ## Seed skills data
	@echo "Seeding skills..."
	@.venv/bin/python -m ingestion.seed_skills

seed-resources: ## Seed resources (use LIMIT=N to limit number)
	@echo "Seeding resources..."
	@.venv/bin/python -m ingestion.ingest --seed ingestion/seed_resources.json --limit $(or $(LIMIT),50)

seed: seed-skills seed-resources ## Seed all data

test-rag: ## Test RAG service
	@cd services/rag && pytest

test-planner: ## Test planner service
	@cd services/planner && pytest

test-quiz: ## Test quiz service
	@cd services/quiz && pytest

test-gateway: ## Test gateway
	@cd gateway && go test ./...

test: test-rag test-planner test-quiz test-gateway ## Run all tests

lint-python: ## Lint Python code
	@cd services/rag && ruff check .
	@cd services/planner && ruff check .
	@cd services/quiz && ruff check .

lint-go: ## Lint Go code
	@cd gateway && golangci-lint run

lint-frontend: ## Lint frontend code
	@cd frontend && npm run lint

lint: lint-python lint-go lint-frontend ## Lint all code

dev-rag: ## Start RAG service in dev mode
	@cd services/rag && ../../.venv/bin/uvicorn main:app --reload --port 8001

dev-planner: ## Start planner service in dev mode
	@cd services/planner && ../../.venv/bin/uvicorn main:app --reload --port 8002

dev-quiz: ## Start quiz service in dev mode
	@cd services/quiz && ../../.venv/bin/uvicorn main:app --reload --port 8003

dev-gateway: ## Start gateway in dev mode
	@cd gateway && go run main.go

dev-frontend: ## Start frontend in dev mode
	@cd frontend && npm run dev

logs: ## Show logs from all services
	docker-compose logs -f

ps: ## Show running services
	docker-compose ps

restart: down up ## Restart all services
