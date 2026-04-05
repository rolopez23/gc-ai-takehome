import uuid

import pytest
from httpx import AsyncClient


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
