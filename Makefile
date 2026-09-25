.PHONY: install test lint check api db-up db-down

install:
	pip install -e ".[dev]"
	pip install httpx

test:
	pytest -q

lint:
	ruff check src tests

check: lint test

api:
	uvicorn src.api.main:app --reload

db-up:
	docker compose up -d db

db-down:
	docker compose down
