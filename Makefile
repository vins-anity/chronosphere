# =============================================================================
# Chronosphere - Developer Commands
# =============================================================================
# Usage: make <command>
# Run `make help` for a list of available commands
# =============================================================================

.PHONY: help dev dev-backend dev-frontend docker-up docker-down docker-logs \
        test lint migrate migrate-new collect train clean install

# Default target
.DEFAULT_GOAL := help

# Colors for terminal output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(CYAN)Chronosphere$(RESET) - Developer Commands"
	@echo ""
	@echo "$(GREEN)Usage:$(RESET) make $(YELLOW)<command>$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Installation
# =============================================================================

install: ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)Installing backend dependencies...$(RESET)"
	uv sync
	@echo "$(GREEN)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(GREEN)Done!$(RESET)"

# =============================================================================
# Development
# =============================================================================

dev: ## Start full dev environment (DB + Redis in Docker, apps locally)
	@echo "$(GREEN)Starting development environment...$(RESET)"
	docker compose up -d db redis
	@echo "$(YELLOW)Waiting for services to be healthy...$(RESET)"
	@sleep 3
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend with hot reload
	@echo "$(GREEN)Starting backend...$(RESET)"
	uv run uvicorn app.ingest.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend dev server
	@echo "$(GREEN)Starting frontend...$(RESET)"
	cd frontend && npm run dev

services: ## Start only DB + Redis (for local development)
	@echo "$(GREEN)Starting database and cache services...$(RESET)"
	docker compose up -d db redis
	@echo "$(GREEN)Services started!$(RESET)"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis:      localhost:6379"

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start full Docker stack (production-like)
	@echo "$(GREEN)Starting Docker stack...$(RESET)"
	docker compose up --build -d

docker-down: ## Stop Docker stack
	@echo "$(YELLOW)Stopping Docker stack...$(RESET)"
	docker compose down

docker-logs: ## View Docker logs (follow mode)
	docker compose logs -f

docker-clean: ## Stop and remove all containers, volumes, and images
	@echo "$(YELLOW)Cleaning Docker resources...$(RESET)"
	docker compose down -v --rmi local
	@echo "$(GREEN)Done!$(RESET)"

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	@echo "$(GREEN)Running migrations...$(RESET)"
	uv run alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	@echo "$(GREEN)Creating new migration...$(RESET)"
	uv run alembic revision --autogenerate -m "$(msg)"

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back migration...$(RESET)"
	uv run alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	docker compose exec db psql -U chronosphere -d chronosphere

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(RESET)"
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	uv run pytest tests/ -v --cov=app --cov-report=html

lint: ## Run linting (ruff)
	@echo "$(GREEN)Running linter...$(RESET)"
	uv run ruff check app/

lint-fix: ## Fix linting issues automatically
	@echo "$(GREEN)Fixing lint issues...$(RESET)"
	uv run ruff check app/ --fix

# =============================================================================
# ML Pipeline
# =============================================================================

collect: ## Run ML data collection
	@echo "$(GREEN)Collecting training data...$(RESET)"
	uv run python -c "from app.ml.collect import main; import asyncio; asyncio.run(main())"

train: ## Train ML model
	@echo "$(GREEN)Training model...$(RESET)"
	uv run python -c "from app.ml.train import train_model; train_model()"

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean generated files and caches
	@echo "$(YELLOW)Cleaning generated files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)Done!$(RESET)"

logs: ## View backend logs (when running locally with uvicorn)
	@tail -f uvicorn_stderr.log uvicorn_stdout.log 2>/dev/null || echo "No log files found"
