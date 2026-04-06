import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from main import app
from models import Contract


@pytest.mark.asyncio
async def test_upload_txt_returns_201(client: AsyncClient):
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("contract.txt", b"contract text here", "text/plain")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "contract_id" in data
    assert "review_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_stores_contract(client: AsyncClient):
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("lease.txt", b"lease content", "text/plain")},
    )
    contract_id = resp.json()["contract_id"]
    detail = await client.get(f"/api/contracts/{contract_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["name"] == "lease.txt"
    assert data["upload_type"] == "txt"


@pytest.mark.asyncio
async def test_upload_with_instructions(client: AsyncClient):
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("contract.txt", b"contract text here", "text/plain")},
        data={"instructions": "Focus on liability"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "review_id" in data


@pytest.mark.asyncio
async def test_upload_rejects_png(client: AsyncClient):
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("image.png", b"fake png data", "image/png")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_rejects_oversized(client: AsyncClient):
    big = b"x" * (10 * 1024 * 1024 + 1)
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("big.txt", big, "text/plain")},
    )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_upload_accepts_pdf(client: AsyncClient):
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("contract.pdf", b"%PDF-1.4 fake pdf", "application/pdf")},
    )
    assert resp.status_code == 201


@pytest_asyncio.fixture
async def db():
    async for session in app.dependency_overrides[get_db]():
        yield session


@pytest.mark.asyncio
async def test_list_contracts_no_blobs(client: AsyncClient):
    await client.post(
        "/api/contracts/upload",
        files={"file": ("contract.txt", b"some text", "text/plain")},
    )
    resp = await client.get("/api/contracts/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    item = data[0]
    assert "name" in item
    assert "upload_type" in item
    assert "review_status" in item
    assert "overall_fairness" in item
    assert "failure_code" in item
    assert "original_blob" not in item
    assert "pdf_blob" not in item


@pytest.mark.asyncio
async def test_get_contract_detail(client: AsyncClient):
    resp = await client.post(
        "/api/contracts/upload",
        files={"file": ("contract.txt", b"full text here", "text/plain")},
    )
    contract_id = resp.json()["contract_id"]
    detail = await client.get(f"/api/contracts/{contract_id}")
    assert detail.status_code == 200
    assert "text" in detail.json()


@pytest.mark.asyncio
async def test_get_contract_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/contracts/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_contracts_includes_review_status(client: AsyncClient):
    await client.post(
        "/api/contracts/upload",
        files={"file": ("contract.txt", b"contract text", "text/plain")},
    )
    resp = await client.get("/api/contracts/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["review_status"] is not None


@pytest.mark.asyncio
async def test_list_contracts_no_review_returns_nulls(
    client: AsyncClient, db: AsyncSession
):
    contract = Contract(
        name="orphan.txt", upload_type="txt", original_blob=b"test", text="text"
    )
    db.add(contract)
    await db.commit()

    resp = await client.get("/api/contracts/")
    assert resp.status_code == 200
    data = resp.json()
    orphan = next(item for item in data if item["name"] == "orphan.txt")
    assert orphan["review_status"] is None
    assert orphan["overall_fairness"] is None
    assert orphan["failure_code"] is None
