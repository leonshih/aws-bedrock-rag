APP_DIR := app
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
IMAGE_NAME := aws-bedrock-rag-api
IMAGE_TAG := latest

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install all dependencies
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Upgrading pip..."
	$(PIP) install --upgrade pip
	@echo "Installing dependencies..."
	$(PIP) install -r $(APP_DIR)/requirements.txt
	@echo "✅ All dependencies installed in $(VENV)"

.PHONY: test
test: ## Run all unit tests
	@echo "Running all tests..."
	$(PYTEST) app/ -v

.PHONY: local
local: ## Run FastAPI locally
	@echo "Starting FastAPI server on http://localhost:8000"
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) ./app
	@echo "✅ Docker image built successfully"

.PHONY: docker-run
docker-run: ## Run Docker container locally
	@echo "Running Docker container on http://localhost:8000"
	docker run -p 8000:8000 --env-file .env $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: deploy-dev
deploy-dev: ## Deploy to dev environment
	@$(MAKE) deploy ENV=dev

.PHONY: deploy-prod
deploy-prod: ## Deploy to prod environment
	@$(MAKE) deploy ENV=prod

.PHONY: clean
clean: ## Clean up virtual environment and caches
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✅ Cleaned up"
