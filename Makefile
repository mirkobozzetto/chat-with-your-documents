# Makefile
.PHONY: help build up down init-db clean

help:
	@echo "Available commands:"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start services"
	@echo "  down      - Stop services"
	@echo "  init-db   - Initialize database tables"
	@echo "  clean     - Clean Docker resources"

build:
	docker-compose build

up:
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

clean:
	docker-compose down -v
	docker system prune -f
