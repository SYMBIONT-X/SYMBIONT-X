.PHONY: help install test lint format clean dev build deploy

help:
	@echo "=== SYMBIONT-X Development Commands ==="
	@echo ""
	@echo "make install  - Install Python + Node dependencies"
	@echo "make test     - Run all tests"
	@echo "make lint     - Run linters (Python + TypeScript)"
	@echo "make format   - Format code (black + isort + prettier)"
	@echo "make clean    - Clean cache and build files"
	@echo "make dev      - Start development servers"
	@echo "make build    - Build for production"
	@echo ""

install:
	pip install -r requirements-dev.txt
	cd src/frontend && npm install

test:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src/ --max-line-length=100
	black src/ --check
	isort src/ --check-only
	cd src/frontend && npm run lint

format:
	black src/ --line-length=100
	isort src/
	cd src/frontend && npm run format

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
	cd src/frontend && rm -rf node_modules dist

dev-backend:
	uvicorn src.agents.orchestrator.main:app --reload --port 8080

dev-frontend:
	cd src/frontend && npm run dev

build:
	cd src/frontend && npm run build

deploy:
	./scripts/build-and-deploy.sh
