.PHONY: help install dev dev-celery dev-frontend stop up-middleware up-ha

BACKEND_SCRIPT := ./backend.sh
CELERY_SCRIPT := ./backend-celery.sh
FRONTEND_SCRIPT := ./frontend.sh
PID_DIR := .noteworks
LOG_DIR := logs
BACKEND_PID_FILE := $(PID_DIR)/backend.pid
CELERY_PID_FILE := $(PID_DIR)/celery.pid
DOCKER_COMPOSE_FILE := deploy/core/docker-compose-core.yml
DEPLOY_MIDDLEWARE_SCRIPT := ./deploy/middleware/deploy-middleware.sh
DEPLOY_HA_SCRIPT := ./deploy/ha/deploy-app-ha.sh

help:
	@echo "NoteWorks Development Commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make dev          - Start backend in foreground mode"
	@echo "  make dev-celery   - Start celery in foreground mode"
	@echo "  make dev-frontend - Start frontend in foreground mode"
	@echo "  make stop         - Stop daemon processes"
	@echo ""
	@echo "Docker Production Commands:"
	@echo "  make up-middleware - Start middleware production services"
	@echo "  make up-ha        - Start HA app production services"

install:
	@echo "Installing backend dependencies..."
	@cd backend && uv sync
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Install complete."

dev:
	@chmod +x "$(BACKEND_SCRIPT)"
	@echo "Starting backend (foreground)..."
	@"$(BACKEND_SCRIPT)"

dev-celery:
	@chmod +x "$(CELERY_SCRIPT)"
	@echo "Starting celery (foreground)..."
	@"$(CELERY_SCRIPT)"

dev-frontend:
	@chmod +x "$(FRONTEND_SCRIPT)"
	@echo "Starting frontend (foreground)..."
	@"$(FRONTEND_SCRIPT)"

stop:
	@if [ -f "$(BACKEND_PID_FILE)" ]; then \
		PID="$$(cat "$(BACKEND_PID_FILE)")"; \
		if kill -0 "$$PID" 2>/dev/null; then \
			kill "$$PID" && echo "Stopped backend ($$PID)"; \
		else \
			echo "Backend PID $$PID is not running"; \
		fi; \
		rm -f "$(BACKEND_PID_FILE)"; \
	else \
		echo "No backend pid file found"; \
	fi
	@if [ -f "$(CELERY_PID_FILE)" ]; then \
		PID="$$(cat "$(CELERY_PID_FILE)")"; \
		if kill -0 "$$PID" 2>/dev/null; then \
			kill "$$PID" && echo "Stopped celery ($$PID)"; \
		else \
			echo "Celery PID $$PID is not running"; \
		fi; \
		rm -f "$(CELERY_PID_FILE)"; \
	else \
		echo "No celery pid file found"; \
	fi

up-middleware:
	@chmod +x "$(DEPLOY_MIDDLEWARE_SCRIPT)"
	@"$(DEPLOY_MIDDLEWARE_SCRIPT)"

up-ha:
	@chmod +x "$(DEPLOY_HA_SCRIPT)"
	@"$(DEPLOY_HA_SCRIPT)"
