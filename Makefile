# Makefile for SAGE project

.PHONY: help setup up down restart logs clean install test

help: ## Show this help message
	@echo "SAGE - Smart Analysis & Generation Engine"
	@echo "=========================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup - create directories and env files
	@echo "Setting up SAGE project..."
	@mkdir -p data/reports data/uploads data/static
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; fi
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; fi
	@chmod +x setup.sh
	@echo "✅ Setup complete!"

up: ## Start all services
	@echo "Starting SAGE services..."
	@docker-compose up -d postgres chromadb backend frontend nginx pgadmin
	@echo "✅ Services started!"
	@echo "Frontend: http://localhost"
	@echo "API Docs: http://localhost/api/v1/docs"
	@echo ""
	@echo "⚠️  Course data not initialized yet."
	@echo "To initialize course data, run: make init-courses"

up-with-courses: ## Start all services and initialize course data
	@echo "Starting SAGE services with course initialization..."
	@docker-compose up -d postgres chromadb backend frontend nginx pgadmin
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Running course worker (scraping + embeddings)..."
	@docker-compose up course_worker
	@echo "✅ All services started and course data initialized!"
	@echo "Frontend: http://localhost"
	@echo "API Docs: http://localhost/api/v1/docs"

init-courses: ## Initialize course data (scrape + create embeddings)
	@echo "Initializing course data..."
	@docker-compose up course_worker
	@echo "✅ Course data initialized!"

down: ## Stop all services
	@echo "Stopping SAGE services..."
	@docker-compose down
	@echo "✅ Services stopped!"

restart: down up ## Restart all services

logs: ## View logs from all services
	@docker-compose logs -f

logs-backend: ## View backend logs
	@docker-compose logs -f backend

logs-frontend: ## View frontend logs
	@docker-compose logs -f frontend

logs-db: ## View database logs
	@docker-compose logs -f postgres

clean: ## Remove all containers, volumes, and build artifacts
	@echo "Cleaning up..."
	@docker-compose down -v
	@rm -rf backend/__pycache__ backend/**/__pycache__
	@rm -rf frontend/node_modules frontend/dist
	@echo "✅ Cleanup complete!"

install-backend: ## Install backend dependencies locally
	@cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies locally
	@cd frontend && npm install

install: install-backend install-frontend ## Install all dependencies locally

test-backend: ## Run backend tests
	@cd backend && pytest

test-frontend: ## Run frontend tests
	@cd frontend && npm test

build: ## Build all Docker images
	@docker-compose build

rebuild: ## Rebuild all Docker images without cache
	@docker-compose build --no-cache

ps: ## Show running containers
	@docker-compose ps

shell-backend: ## Open shell in backend container
	@docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	@docker-compose exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U sage_user -d sage_db

migrate: ## Run database migrations
	@docker-compose exec backend alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

backup-db: ## Backup PostgreSQL database
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U sage_user sage_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up to backups/"

restore-db: ## Restore PostgreSQL database (specify BACKUP_FILE=path/to/backup.sql)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify BACKUP_FILE=path/to/backup.sql"; \
		exit 1; \
	fi
	@docker-compose exec -T postgres psql -U sage_user -d sage_db < $(BACKUP_FILE)
	@echo "✅ Database restored!"

dev: ## Start in development mode with live reload
	@make up
	@make logs

prod: ## Start in production mode
	@docker-compose -f docker-compose.prod.yml up -d

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -f http://localhost/health || echo "❌ Nginx failed"
	@curl -f http://localhost/api/v1/health || echo "❌ Backend failed"
	@curl -f http://localhost:8001/api/v1/heartbeat || echo "❌ ChromaDB failed"
	@docker-compose exec postgres pg_isready -U sage_user || echo "❌ PostgreSQL failed"
	@echo "✅ Health check complete!"

scrape-courses: ## Run course scraper for all departments and semesters
	@echo "Scraping courses from TED University..."
	@cd scraper && python scrape_multi_semester.py
	@echo "✅ Scraping complete! Check tedu_*_courses_metadata.json files"

create-embeddings: ## Generate embeddings and populate ChromaDB + PostgreSQL
	@echo "Creating course embeddings..."
	@docker-compose exec backend python scripts/create_course_embeddings.py
	@echo "✅ Embeddings created and stored!"

setup-courses: scrape-courses create-embeddings ## Full course setup: scrape + create embeddings

check-embeddings: ## Check embedding system status
	@echo "Checking embeddings status..."
	@curl -s http://localhost/api/v1/courses/status | python -m json.tool

