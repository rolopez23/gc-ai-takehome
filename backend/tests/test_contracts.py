import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_contract(client: AsyncClient):
    resp = await client.post("/api/contracts/", json={
        "name": "Test Contract",
        "vendor": "Acme Corp",
        "customer": "Widgets Inc",
        "agreement_type": "SaaS MSA",
        "text": "This is the contract text.",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Contract"
    assert data["vendor"] == "Acme Corp"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_contracts(client: AsyncClient):
    await client.post("/api/contracts/", json={
        "name": "Contract A",
        "text": "Text A",
    })
    resp = await client.get("/api/contracts/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_contract(client: AsyncClient):
    create_resp = await client.post("/api/contracts/", json={
        "name": "Detail Test",
        "text": "Full text here.",
    })
    contract_id = create_resp.json()["id"]
    resp = await client.get(f"/api/contracts/{contract_id}")
    assert resp.status_code == 200
    assert resp.json()["text"] == "Full text here."


@pytest.mark.asyncio
async def test_get_contract_not_found(client: AsyncClient):
    resp = await client.get("/api/contracts/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
