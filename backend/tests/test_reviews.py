import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_review(client: AsyncClient):
    contract = await client.post("/api/contracts/", json={
        "name": "Review Test",
        "text": "Contract text.",
    })
    contract_id = contract.json()["id"]

    resp = await client.post(f"/api/reviews/contracts/{contract_id}/review")
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_get_review(client: AsyncClient):
    contract = await client.post("/api/contracts/", json={
        "name": "Get Review Test",
        "text": "Contract text.",
    })
    contract_id = contract.json()["id"]

    review_resp = await client.post(f"/api/reviews/contracts/{contract_id}/review")
    review_id = review_resp.json()["id"]

    resp = await client.get(f"/api/reviews/{review_id}")
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.asyncio
async def test_create_review_contract_not_found(client: AsyncClient):
    resp = await client.post("/api/reviews/contracts/00000000-0000-0000-0000-000000000000/review")
    assert resp.status_code == 404
