# Makefile
.PHONY: help build up down init-db clean dev dev-down local rebuild

help:
	@echo "🚀 RAG Development Commands:"
	@echo "  dev       - Start Postgres + run Streamlit locally"
	@echo "  up        - Full Docker stack"
	@echo "  rebuild   - Force rebuild + start (for code changes)"
	@echo "  down      - Stop everything"
	@echo "  clean     - Nuclear clean"

build:
	docker-compose build

up:
	@echo "🐳 Starting full Docker stack..."
	docker-compose up -d

down:
	docker-compose down

init-db:
	docker-compose exec rag-app python scripts/db/init_db.py

migrate-auth:
	docker-compose exec rag-app python scripts/db/migrate_auth.py

create-user:
	@echo "Usage: make create-user USER=username PASS=password"
	@if [ -z "$(USER)" ] || [ -z "$(PASS)" ]; then \
		echo "❌ Missing USER or PASS variables"; \
		echo "Example: make create-user USER=admin PASS=mypassword"; \
		exit 1; \
	fi
	docker-compose exec rag-app python scripts/db/create_user.py $(USER) $(PASS)

dev:
	@echo "🚀 Dev mode: Postgres + local Streamlit"
	docker-compose up -d postgres
	@echo "✅ Postgres ready on :5433"
	uv run streamlit run app.py

rebuild:
	@echo "🔄 Force rebuild for code changes..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

clean:
	docker-compose down -v
	docker system prune -f

