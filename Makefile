.PHONY: help install test local docker-build deploy destroy clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## Activate virtual environment (use: source .venv/bin/activate)
	@echo "To activate virtual environment, run:"
	@echo "  source .venv/bin/activate"

install: ## Install all dependencies (CDK + FastAPI)
	@echo "Installing CDK dependencies..."
	pip install -r requirements.txt
	@echo "Installing FastAPI dependencies..."
	pip install -r app/requirements.txt
	@echo "✅ All dependencies installed"

test: ## Run local tests
	@echo "Running tests..."
	cd app && python -m pytest tests/ -v

local: ## Run FastAPI locally
	@echo "Starting FastAPI server on http://localhost:8000"
	cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	docker build -t aws-bedrock-rag-api:latest ./app
	@echo "✅ Docker image built successfully"

docker-run: ## Run Docker container locally
	@echo "Running Docker container on http://localhost:8000"
	docker run -p 8000:8000 --env-file .env aws-bedrock-rag-api:latest

deploy: ## Deploy to AWS using CDK
	@echo "Deploying to AWS..."
	cdk deploy --all --require-approval never
	@echo "✅ Deployment complete"

synth: ## Synthesize CloudFormation template
	@echo "Synthesizing CloudFormation template..."
	cdk synth

diff: ## Show differences between deployed and local stack
	cdk diff

bootstrap: ## Bootstrap CDK (first time only)
	@echo "Bootstrapping CDK..."
	cdk bootstrap
	@echo "✅ CDK bootstrap complete"

destroy: ## Destroy all AWS resources
	@echo "⚠️  Destroying all AWS resources..."
	cdk destroy --all --force

clean: ## Clean up local build artifacts
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf cdk.out .cdk.staging
	@echo "✅ Cleanup complete"
