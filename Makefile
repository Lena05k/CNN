.PHONY: help build up down logs restart clean rebuild shell-backend shell-frontend

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Показать список команд
	@echo "$(BLUE)CNN Classifier - Docker Commands$(NC)"
	@echo "================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

build: ## Собрать Docker-контейнеры
	@echo "$(YELLOW)Сборка контейнеров...$(NC)"
	docker-compose build

up: ## Запустить контейнеры в фоновом режиме
	@echo "$(GREEN)Запуск контейнеров...$(NC)"
	docker-compose up -d
	@echo ""
	@echo "$(BLUE)Доступ к приложению:$(NC)"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8001"
	@echo "  Admin:    http://localhost:8001/admin"

up-verbose: ## Запустить контейнеры в foreground режиме с логами
	docker-compose up

down: ## Остановить и удалить контейнеры
	@echo "$(YELLOW)Остановка контейнеров...$(NC)"
	docker-compose down

logs: ## Показать логи контейнеров
	docker-compose logs -f

logs-backend: ## Показать логи backend контейнера
	docker-compose logs -f backend

logs-frontend: ## Показать логи frontend контейнера
	docker-compose logs -f frontend

restart: ## Перезапустить контейнеры
	docker-compose restart

clean: ## Остановить контейнеры и удалить volumes
	@echo "$(YELLOW)Очистка всех ресурсов Docker...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Готово!$(NC)"

rebuild: ## Пересобрать и перезапустить контейнеры
	@echo "$(YELLOW)Пересборка и перезапуск...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

shell-backend: ## Открыть shell в backend контейнере
	docker-compose exec backend sh

shell-frontend: ## Открыть shell в frontend контейнере
	docker-compose exec frontend sh

migrate: ## Выполнить миграции Django
	docker-compose exec backend python manage.py migrate

createsuperuser: ## Создать суперпользователя Django
	docker-compose exec backend python manage.py createsuperuser

collectstatic: ## Собрать статические файлы Django
	docker-compose exec backend python manage.py collectstatic --noinput

test: ## Запустить тесты Django
	docker-compose exec backend python manage.py test

install-backend: ## Установить Python-зависимости локально
	pip install -r requirements.txt

install-frontend: ## Установить Node-зависимости локально
	cd frontend && npm install

dev-backend: ## Запустить Django локально
	python manage.py runserver

dev-frontend: ## Запустить Vite локально
	cd frontend && npm run dev
