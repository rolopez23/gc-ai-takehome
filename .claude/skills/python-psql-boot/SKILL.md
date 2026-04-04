---
name: python-psql-boot
description: >
  Scaffold a Python / FastAPI / PostgreSQL backend from scratch. Trigger when the user asks to
  bootstrap, scaffold, or create a new backend, API, or Python server. Also trigger when the
  user says "boot backend", "new backend", "create backend", "scaffold backend", or
  "new API".
---

# Python + FastAPI + PostgreSQL Backend Boot

Use this skill to scaffold a backend that follows these exact patterns and conventions.
Do not deviate unless instructed.

## Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI with async support
- **Server:** Uvicorn (ASGI)
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy 2.0+ with async engine (`create_async_engine`, `AsyncSession`)
- **Async driver:** asyncpg
- **Migrations:** Alembic
- **Package manager:** uv (`pyproject.toml`)
- **Testing:** pytest + pytest-asyncio + httpx (async test client)
- **Env vars:** python-dotenv

## Project Layout

```
backend/
├── main.py                  # FastAPI app, lifespan, router registration
├── database.py              # engine, AsyncSessionLocal, Base (DeclarativeBase)
├── models.py                # SQLAlchemy ORM models (all in one file unless large)
├── schemas.py               # Pydantic request/response schemas (all in one file)
├── .env                     # DATABASE_URL and other env vars
├── pyproject.toml
├── alembic.ini
├── routers/
│   └── <resource>.py        # One file per resource
├── services/
│   └── <service>.py         # Business logic, no DB imports in routers
├── migrations/
│   ├── env.py
│   └── versions/
└── tests/
    ├── conftest.py          # Shared fixtures
    └── test_<resource>.py
```

## Conventions

### Models (`models.py`)

- All models inherit from a shared `Base = DeclarativeBase()`
- Every table has `id: UUID` (default `uuid.uuid4()`) as primary key
- Every table has `created_at: datetime` (timezone-aware, default `datetime.now(UTC)`)
- Use `mapped_column()` and `Mapped[T]` type annotations (SQLAlchemy 2.0 style)
- Nullable fields: `Mapped[str | None]`
- Foreign keys: `ForeignKey("table.id")` with matching `relationship()` on both sides

### Schemas (`schemas.py`)

- Separate `<Model>Create` (input) and `<Model>Out` (output) Pydantic models
- `<Model>Out` has `model_config = ConfigDict(from_attributes=True)` for ORM serialization
- UUIDs and datetimes serialize naturally via Pydantic v2

### Routers (`routers/<resource>.py`)

- `router = APIRouter(prefix="/resource", tags=["resource"])`
- Inject `db: AsyncSession = Depends(get_db)` in every route
- Return HTTP 201 for POST, 200 for GET, 404 with `HTTPException` if not found
- No business logic in routers — delegate to services

### Database (`database.py`)

```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/app")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = DeclarativeBase()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Lifespan (`main.py`)

- On startup: execute `SELECT 1` to verify DB connectivity; fail fast if unreachable
- On shutdown: dispose engine

### CORS

- Allow origins from `FRONTEND_URL` env var (default `http://localhost:3000`)
- `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`

### Tests (`tests/`)

- `conftest.py` sets up an in-memory or test-DB async session, overrides `get_db`
- Use `httpx.AsyncClient(app=app, base_url="http://test")` as the test client
- Tests are async (`@pytest.mark.asyncio`)
- One test file per router

### Migrations

- Each schema change is a separate Alembic migration
- Migration filenames describe the change: `add_email_to_users.py`
- `alembic upgrade head` is the only required command for fresh setup

### Docker Compose

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## Scaffolding Steps

When bootstrapping, ask the user for:

1. **Domain description** — what the app does
2. **Entities and fields** — each entity, its fields, types, and relationships
3. **Endpoints needed** — method, path, and what it does
4. **Business logic** — any non-trivial rules

Then produce the following files in order:

1. `pyproject.toml`
2. `docker-compose.yml`
3. `backend/.env`
4. `backend/database.py`
5. `backend/models.py`
6. `backend/schemas.py`
7. `backend/main.py`
8. One file per router under `backend/routers/`
9. One service file per non-trivial business logic under `backend/services/`
10. `backend/migrations/env.py` and one initial Alembic migration
11. `backend/tests/conftest.py` and one test file per router

Do not add features or endpoints not listed by the user. Do not add auth unless asked.
