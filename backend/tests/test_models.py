import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload, undefer

from models import Contract, ContractReview, ReviewClause
from tests.conftest import TestSessionLocal

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session


async def test_create_contract_with_blobs(db):
    blob = b"%PDF-1.4 fake content"
    c = Contract(
        name="agreement.pdf",
        upload_type="pdf",
        original_blob=blob,
        pdf_blob=blob,
        text="extracted text",
    )
    db.add(c)
    await db.commit()

    row = await db.get(Contract, c.id)
    assert row is not None
    assert row.name == "agreement.pdf"
    assert row.upload_type == "pdf"
    assert row.original_blob == blob
    assert row.pdf_blob == blob
    assert row.text == "extracted text"
    assert isinstance(row.id, uuid.UUID)
    assert isinstance(row.created_at, datetime)


async def test_contract_txt_has_text_no_pdf_blob(db):
    c = Contract(
        name="readme.txt",
        upload_type="txt",
        original_blob=b"plain text content",
        text="plain text content",
    )
    db.add(c)
    await db.commit()

    stmt = (
        select(Contract)
        .where(Contract.id == c.id)
        .options(undefer(Contract.pdf_blob))
    )
    result = await db.execute(stmt)
    row = result.scalar_one()
    assert row.upload_type == "txt"
    assert row.text == "plain text content"
    assert row.pdf_blob is None


async def test_create_review_pending(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(contract_id=c.id)
    db.add(r)
    await db.commit()

    row = await db.get(ContractReview, r.id)
    assert row.status == "pending"
    assert row.overall_fairness is None
    assert row.summary is None
    assert row.call_to_action is None
    assert row.failure_message is None
    assert row.completed_at is None
    assert row.review_instructions is None


async def test_review_completed_success(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(
        contract_id=c.id,
        status="completed",
        overall_fairness="fair",
        summary="Looks good overall.",
        call_to_action={"action": "sign"},
        completed_at=datetime.now(UTC),
    )
    db.add(r)
    await db.commit()

    row = await db.get(ContractReview, r.id)
    assert row.status == "completed"
    assert row.overall_fairness == "fair"
    assert row.summary == "Looks good overall."
    assert row.call_to_action == {"action": "sign"}
    assert row.completed_at is not None


async def test_review_completed_not_a_contract(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(
        contract_id=c.id,
        status="completed",
        overall_fairness=None,
        summary="This does not appear to be a contract.",
        completed_at=datetime.now(UTC),
    )
    db.add(r)
    await db.commit()

    row = await db.get(ContractReview, r.id)
    assert row.status == "completed"
    assert row.overall_fairness is None
    assert row.summary == "This does not appear to be a contract."


async def test_review_failed(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(
        contract_id=c.id,
        status="failed",
        failure_message="LLM timeout",
    )
    db.add(r)
    await db.commit()

    row = await db.get(ContractReview, r.id)
    assert row.status == "failed"
    assert row.failure_message == "LLM timeout"


async def test_review_instructions(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(
        contract_id=c.id,
        review_instructions="Focus on liability clauses.",
    )
    db.add(r)
    await db.commit()

    row = await db.get(ContractReview, r.id)
    assert row.review_instructions == "Focus on liability clauses."


async def test_create_review_clause(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(contract_id=c.id, status="completed")
    db.add(r)
    await db.commit()

    clause = ReviewClause(
        review_id=r.id,
        section_number="3.1",
        clause_type="liability",
        purpose="Limits vendor liability to contract value.",
        fairness="non-standard",
        market_standard="Typically liability is capped at 2x contract value.",
        explanation="The cap is unusually low for this type of agreement.",
    )
    db.add(clause)
    await db.commit()

    row = await db.get(ReviewClause, clause.id)
    assert row.section_number == "3.1"
    assert row.clause_type == "liability"
    assert row.purpose == "Limits vendor liability to contract value."
    assert row.fairness == "non-standard"
    assert row.market_standard == "Typically liability is capped at 2x contract value."
    assert row.explanation == "The cap is unusually low for this type of agreement."


async def test_clause_relationship(db):
    c = Contract(name="f.pdf", upload_type="pdf", original_blob=b"x")
    db.add(c)
    await db.commit()

    r = ContractReview(contract_id=c.id, status="completed")
    db.add(r)
    await db.commit()

    db.add_all([
        ReviewClause(
            review_id=r.id,
            section_number="1.0",
            clause_type="termination",
            purpose="Allows either party to terminate.",
            fairness="fair",
            market_standard="Standard mutual termination clause.",
            explanation="This is standard.",
        ),
        ReviewClause(
            review_id=r.id,
            section_number="2.0",
            clause_type="indemnification",
            purpose="One-sided indemnification.",
            fairness="dealbreaker",
            market_standard="Mutual indemnification is standard.",
            explanation="Only one party bears indemnification burden.",
        ),
    ])
    await db.commit()

    stmt = (
        select(ContractReview)
        .where(ContractReview.id == r.id)
        .options(selectinload(ContractReview.clauses))
    )
    result = await db.execute(stmt)
    loaded = result.scalar_one()
    assert len(loaded.clauses) == 2
