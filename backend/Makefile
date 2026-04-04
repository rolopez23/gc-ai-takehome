setup:
	uv sync --extra dev

db:
	docker compose -f ../docker-compose.yml up -d db
	uv run alembic upgrade head

dev:
	portless contract-evaluator-server uv run uvicorn main:app --reload
