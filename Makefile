APP_DIR := app
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MYPY := $(VENV)/bin/mypy
RUFF := $(VENV)/bin/ruff
PRECOMMIT := $(VENV)/bin/pre-commit
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

.PHONY: install-dev
install-dev: install ## Install development dependencies (mypy, ruff, pre-commit)
	@echo "Installing development tools..."
	$(PIP) install mypy ruff pre-commit
	@echo "Installing pre-commit hooks..."
	$(PRECOMMIT) install
	@echo "✅ Development tools installed"

.PHONY: test
test: ## Run all unit tests
	@echo "Running all tests..."
	PYTHONPATH=. $(PYTEST) app/ -v

.PHONY: test-contract
test-contract: ## Run only contract tests
	@echo "Running contract tests..."
	PYTHONPATH=. $(PYTEST) app/ -v -m contract

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	PYTHONPATH=. $(PYTEST) app/ --cov=app --cov-report=term-missing --cov-report=html

.PHONY: typecheck
typecheck: ## Run mypy type checking
	@echo "Running type checks with mypy..."
	$(MYPY) app/ --strict --ignore-missing-imports

.PHONY: lint
lint: ## Run ruff linter
	@echo "Running ruff linter..."
	$(RUFF) check app/

.PHONY: lint-fix
lint-fix: ## Auto-fix linting issues
	@echo "Auto-fixing linting issues..."
	$(RUFF) check app/ --fix

.PHONY: format
format: ## Format code with ruff
	@echo "Formatting code..."
	$(RUFF) format app/

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks manually
	@echo "Running pre-commit hooks..."
	$(PRECOMMIT) run --all-files

.PHONY: quality
quality: typecheck lint test ## Run all quality checks (typecheck + lint + test)
	@echo "✅ All quality checks passed"

.PHONY: local
local: ## Run FastAPI locally
	@echo "Starting FastAPI server on http://localhost:8000"
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info

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
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov coverage.json
	@echo "✅ Cleaned up"
