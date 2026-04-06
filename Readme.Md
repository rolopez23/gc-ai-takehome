# GC.AI Contract Evaluator

AI-powered contract analysis tool that evaluates vendor contracts against a defined playbook of 132 checks across 4 agreement types (SaaS MSA, Mutual NDA, Commercial MSA, DPA).

Built with the [Agent Harness](https://github.com/rolopez23/agent-harness) workflow.

## Stack

| Layer    | Tech                                                         |
| -------- | ------------------------------------------------------------ |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS v4, Turbopack |
| Backend  | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic       |
| Database | PostgreSQL 16 (asyncpg)                                      |
| AI       | Claude (Anthropic API)                                        |
| Package  | npm (frontend), uv (backend)                                 |

## Prerequisites

- Node.js 18+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (for PostgreSQL)
- An [Anthropic API key](https://console.anthropic.com/)

## Quick Start

### 1. Backend

```bash
cd backend
make setup    # prompts for API key if missing, installs Python deps + LibreOffice
make db       # start Postgres via Docker + run migrations
make dev      # start API server on http://localhost:8000
```

`make setup` will check for a `.env` file with a valid `ANTHROPIC_API_KEY`. If one isn't found, it will prompt you to paste your key. You can also copy the template manually:

```bash
cp .env.tmpl .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev   # start dev server on http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000) and upload a contract.

## Running Tests

```bash
# Backend (uses in-memory SQLite — no Postgres required)
cd backend
uv run pytest tests/ -v

# Frontend
cd frontend
npm test
```

## Domain

The app evaluates contracts against the GC AI Playbook (`docs/gc-ai-takehome/gc_ai_playbook.md`), which defines 132 checks across four agreement types:

- **SaaS Master Service Agreement** (21 checks)
- **Mutual Non-Disclosure Agreement** (15 checks)
- **Commercial Master Services Agreement** (80 checks)
- **Data Processing Agreement** (16 checks)

Each check produces a result with a status (`PASS`, `TRIGGERED`, `PARTIAL`, `ABSENT`), severity score (1-10), quoted contract language, and a recommended redline. See `docs/gc-ai-takehome/contract_eval_prompt.md` for the full evaluation prompt schema.

## Demo Video

[Demo Video](https://drive.google.com/file/d/1W1fRnZdeumqCRJ5Ls5BvU0hRyd8rQgl6/view?usp=drive_link)
