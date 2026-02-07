.PHONY: help install dev up down logs test clean check-secrets expose

help:
	@echo "NeverDown Development Commands"
	@echo "=============================="
	@echo "make install       - Install dependencies"
	@echo "make dev           - Start local development server"
	@echo "make up            - Start services with Docker Compose"
	@echo "make down          - Stop services"
	@echo "make logs          - View logs"
	@echo "make test          - Run tests"
	@echo "make clean         - Clean up temporary files"
	@echo "make check-secrets - Scan for secrets in codebase"
	@echo "make expose        - Expose local server via ngrok"

install:
	pip install -e ".[dev]"

dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

check-secrets:
	# Run the Sanitizer agent on the current directory
	python -m agents.agent_0_sanitizer.sanitizer --scan-only .

expose:
	@echo "Starting ngrok on port 8000..."
	@echo "Copy the HTTPS URL from the output below and use it as your Payload URL."
	ngrok http 8000
