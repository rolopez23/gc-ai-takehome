import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from main import app
from models import Contract, ContractReview, ReviewClause


@pytest_asyncio.fixture
async def db():
    async for session in app.dependency_overrides[get_db]():
        yield session


@pytest.mark.asyncio
async def test_get_review_pending(client: AsyncClient, db: AsyncSession):
    contract = Contract(
        name="test.txt", upload_type="txt", original_blob=b"test", text="test text"
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(contract_id=contract.id, status="pending")
    db.add(review)
    await db.commit()

    resp = await client.get(f"/api/reviews/{review.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["clauses"] == []


@pytest.mark.asyncio
async def test_get_review_completed(client: AsyncClient, db: AsyncSession):
    contract = Contract(
        name="test.txt", upload_type="txt", original_blob=b"test", text="test text"
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(
        contract_id=contract.id,
        status="completed",
        overall_fairness="fair",
        summary="This contract is fair overall.",
        call_to_action=[{"label": "Sign it", "url": "https://example.com"}],
    )
    db.add(review)
    await db.flush()
    clause1 = ReviewClause(
        review_id=review.id,
        section_number="1.1",
        clause_type="termination",
        purpose="Defines termination terms",
        fairness="fair",
        market_standard="Standard 30-day notice",
        explanation="This clause is standard.",
    )
    clause2 = ReviewClause(
        review_id=review.id,
        section_number="2.1",
        clause_type="liability",
        purpose="Defines liability limits",
        fairness="non-standard",
        market_standard="Typically capped at contract value",
        explanation="Liability is uncapped, which is unusual.",
    )
    db.add_all([clause1, clause2])
    await db.commit()

    resp = await client.get(f"/api/reviews/{review.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_fairness"] == "fair"
    assert data["summary"] == "This contract is fair overall."
    assert data["call_to_action"] == [
        {"label": "Sign it", "url": "https://example.com"}
    ]
    assert len(data["clauses"]) == 2


@pytest.mark.asyncio
async def test_get_review_rejected(client: AsyncClient, db: AsyncSession):
    contract = Contract(
        name="test.txt", upload_type="txt", original_blob=b"test", text="test text"
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(
        contract_id=contract.id,
        status="completed",
        overall_fairness=None,
    )
    db.add(review)
    await db.commit()

    resp = await client.get(f"/api/reviews/{review.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_fairness"] is None
    assert data["clauses"] == []


@pytest.mark.asyncio
async def test_get_review_failed(client: AsyncClient, db: AsyncSession):
    contract = Contract(
        name="test.txt", upload_type="txt", original_blob=b"test", text="test text"
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(
        contract_id=contract.id,
        status="failed",
        failure_message="LLM returned invalid JSON",
    )
    db.add(review)
    await db.commit()

    resp = await client.get(f"/api/reviews/{review.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["failure_message"] == "LLM returned invalid JSON"


@pytest.mark.asyncio
async def test_get_review_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/reviews/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_review_by_contract_id(client: AsyncClient, db: AsyncSession):
    contract = Contract(
        name="test.txt", upload_type="txt", original_blob=b"test", text="test text"
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(contract_id=contract.id, status="pending")
    db.add(review)
    await db.commit()

    resp = await client.get(f"/api/contracts/{contract.id}/review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(review.id)
    assert data["contract_id"] == str(contract.id)


@pytest.mark.asyncio
async def test_get_review_by_contract_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/contracts/{fake_id}/review")
    assert resp.status_code == 404
