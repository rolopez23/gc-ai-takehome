setup:
	uv sync --extra dev
	@command -v libreoffice >/dev/null 2>&1 || (echo "Installing LibreOffice (required for DOC/DOCX conversion)..." && brew install --cask libreoffice)

db:
	docker compose -f ../docker-compose.yml up -d db
	uv run alembic upgrade head

reset-db:
	docker compose -f ../docker-compose.yml down -v
	docker compose -f ../docker-compose.yml up -d db
	sleep 2
	uv run alembic upgrade head

dev:
	portless contract-evaluator-server uv run uvicorn main:app --reload
