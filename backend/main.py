import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import engine

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB connectivity on startup
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


app = FastAPI(title="GC AI Takehome", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
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
