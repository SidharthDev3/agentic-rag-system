.PHONY: install dev test lint format evaluate ingest docker-up docker-down

install:

	python -m pip install -r backend/requirements.txt

	cd frontend && npm install

dev:

	docker compose up --build

test:

	cd backend && python -m pytest -q

lint:

	cd backend && ruff check app tests

format:

	cd backend && ruff format app tests

evaluate:

	cd backend && python -m app.evaluation.run

ingest:

	python scripts/ingest_samples.py

docker-up:

	docker compose up --build

docker-down:

	docker compose down
