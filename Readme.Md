# GC.AI Contract Evaluator

AI-powered contract analysis tool that evaluates vendor contracts against a defined playbook of 132 checks across 4 agreement types (SaaS MSA, Mutual NDA, Commercial MSA, DPA).

## Stack

| Layer    | Tech                                                        |
|----------|-------------------------------------------------------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS v4, Turbopack |
| Backend  | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic     |
| Database | PostgreSQL 16 (asyncpg)                                     |
| Package  | npm (frontend), uv (backend)                                |

## Prerequisites

- Node.js 18+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (for PostgreSQL)

## Setup

### 1. Database

```bash
docker compose up -d db
```

Starts PostgreSQL on `localhost:5432` with user/password/db all set to `app`.

### 2. Backend

```bash
cd backend
uv sync --extra dev
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server runs at `http://localhost:3000`.

### 4. Portless (local dev URLs)

```bash
portless
```

This proxies both services through friendly local URLs:

| Service  | URL                                          |
|----------|----------------------------------------------|
| Frontend | `http://contract-evaluator.localhost`         |
| Backend  | `http://contract-evaluator-server.localhost`  |

## Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

Tests use an in-memory SQLite database and don't require PostgreSQL.

## Domain

The app evaluates contracts against the GC AI Playbook (`docs/gc-ai-takehome/gc_ai_playbook.md`), which defines 132 checks across four agreement types:

- **SaaS Master Service Agreement** (21 checks)
- **Mutual Non-Disclosure Agreement** (15 checks)
- **Commercial Master Services Agreement** (80 checks)
- **Data Processing Agreement** (16 checks)

Each check produces a result with a status (`PASS`, `TRIGGERED`, `PARTIAL`, `ABSENT`), severity score (1-10), quoted contract language, and a recommended redline. See `docs/gc-ai-takehome/contract_eval_prompt.md` for the full evaluation prompt schema.
