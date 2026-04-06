import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import engine

load_dotenv()


def _check_api_key():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    if not key.startswith("sk-ant-"):
        raise RuntimeError(
            f"ANTHROPIC_API_KEY looks invalid (starts with '{key[:6]}...'). Expected 'sk-ant-...'."
        )
    logger = logging.getLogger("uvicorn.error")
    logger.info("Valid Anthropic API key found (sk-ant-...)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_api_key()
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


app = FastAPI(title="GC AI Takehome", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"https?://localhost(:\d+)?"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import contracts, reviews  # noqa: E402

app.include_router(contracts.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
