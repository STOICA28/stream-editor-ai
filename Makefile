.PHONY: up down dev install migrate test lint format check-vault test-all

up:
	docker-compose up -d

down:
	docker-compose down

dev:
	docker-compose up -d postgres redis

install:
	uv sync
	cd apps/web && npm install

migrate:
	cd apps/api && uv run alembic upgrade head

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check .
	uv run mypy packages/ apps/

format:
	uv run ruff format .

check-vault:
	uv run python scripts/check_vault.py

test-all: test lint check-vault
