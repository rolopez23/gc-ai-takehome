import json
import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from main import app
from models import Contract, ContractReview


@pytest_asyncio.fixture
async def db():
    async for session in app.dependency_overrides[get_db]():
        yield session


async def _make_review(db: AsyncSession, status: str = "pending") -> ContractReview:
    """Helper: create a Contract + ContractReview with given status."""
    contract = Contract(
        name="test.txt", upload_type="txt", original_blob=b"test", text="test text"
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(contract_id=contract.id, status=status)
    db.add(review)
    await db.commit()
    return review


# --- Cycle 1: 404 and status guards ---


@pytest.mark.asyncio
async def test_stream_review_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/reviews/{fake_id}/stream")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stream_already_completed(client: AsyncClient, db: AsyncSession):
    review = await _make_review(db, status="completed")
    resp = await client.get(f"/api/reviews/{review.id}/stream")
    assert resp.status_code == 409
    assert "already" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_already_rejected(client: AsyncClient, db: AsyncSession):
    review = await _make_review(db, status="rejected")
    resp = await client.get(f"/api/reviews/{review.id}/stream")
    assert resp.status_code == 409
    assert "already" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_already_failed(client: AsyncClient, db: AsyncSession):
    review = await _make_review(db, status="failed")
    resp = await client.get(f"/api/reviews/{review.id}/stream")
    assert resp.status_code == 409
    assert "already" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_already_in_progress(client: AsyncClient, db: AsyncSession):
    review = await _make_review(db, status="evaluating")
    resp = await client.get(f"/api/reviews/{review.id}/stream")
    assert resp.status_code == 409
    assert "already in progress" in resp.json()["detail"].lower()


# --- Cycle 2: Streaming happy path ---


async def _mock_run(self):
    """Mock orchestrator that yields two NDJSON lines."""
    yield json.dumps({"event": "started", "review_id": str(self.review_id)}) + "\n"
    yield json.dumps({"event": "completed", "result": {}}) + "\n"


@pytest.mark.asyncio
async def test_stream_returns_ndjson(client: AsyncClient, db: AsyncSession):
    review = await _make_review(db, status="pending")
    with patch("routers.reviews.PipelineOrchestrator.run", _mock_run):
        resp = await client.get(f"/api/reviews/{review.id}/stream")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/x-ndjson"


@pytest.mark.asyncio
async def test_stream_emits_events(client: AsyncClient, db: AsyncSession):
    review = await _make_review(db, status="pending")
    with patch("routers.reviews.PipelineOrchestrator.run", _mock_run):
        resp = await client.get(f"/api/reviews/{review.id}/stream")
    lines = [line for line in resp.text.strip().split("\n") if line]
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["event"] == "started"
    assert first["review_id"] == str(review.id)
    assert second["event"] == "completed"


# --- Cycle 3: Backward compatibility ---


@pytest.mark.asyncio
async def test_existing_upload_unchanged(client: AsyncClient):
    """POST /api/contracts/upload still returns 201 with expected shape."""
    # Use a minimal text file upload
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("test.txt", b"This is a test contract.", "text/plain")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "contract_id" in data
    assert "review_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_existing_polling_unchanged(client: AsyncClient, db: AsyncSession):
    """GET /api/reviews/{id} still returns review JSON."""
    review = await _make_review(db, status="pending")
    resp = await client.get(f"/api/reviews/{review.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(review.id)
    assert data["status"] == "pending"
