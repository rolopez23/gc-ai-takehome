import uuid
from datetime import UTC, datetime

from schemas import (
    ClauseOut,
    ContractDetailOut,
    ContractOut,
    ReviewDetailOut,
    ReviewOut,
    UploadResponse,
)


def test_upload_response():
    cid = uuid.uuid4()
    rid = uuid.uuid4()
    resp = UploadResponse(contract_id=cid, review_id=rid, status="pending")
    data = resp.model_dump()
    assert data["contract_id"] == cid
    assert data["review_id"] == rid
    assert data["status"] == "pending"


def test_contract_out_excludes_blobs():
    fields = ContractOut.model_fields
    assert "original_blob" not in fields
    assert "pdf_blob" not in fields


def test_review_out_completed():
    now = datetime.now(UTC)
    review = ReviewOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="completed",
        review_instructions=None,
        overall_fairness="fair",
        summary="Looks good",
        call_to_action=["Fix 3.1"],
        failure_message=None,
        created_at=now,
        completed_at=now,
    )
    data = review.model_dump()
    assert data["status"] == "completed"
    assert data["overall_fairness"] == "fair"
    assert data["call_to_action"] == ["Fix 3.1"]


def test_review_out_rejected():
    now = datetime.now(UTC)
    review = ReviewOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="rejected",
        review_instructions=None,
        overall_fairness=None,
        summary=None,
        call_to_action=None,
        failure_message=None,
        created_at=now,
        completed_at=None,
    )
    data = review.model_dump()
    assert data["overall_fairness"] is None


def test_review_out_failed():
    now = datetime.now(UTC)
    review = ReviewOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="failed",
        review_instructions=None,
        overall_fairness=None,
        summary=None,
        call_to_action=None,
        failure_message="timeout",
        created_at=now,
        completed_at=None,
    )
    data = review.model_dump()
    assert data["status"] == "failed"
    assert data["failure_message"] == "timeout"


def test_review_detail_with_clauses():
    now = datetime.now(UTC)
    clause = ClauseOut(
        id=uuid.uuid4(),
        section_number="3.1",
        clause_type="liability",
        purpose="Limits liability",
        fairness="fair",
        market_standard="Standard cap at 1x",
        explanation="This clause is standard.",
    )
    review = ReviewDetailOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="completed",
        review_instructions=None,
        overall_fairness="fair",
        summary="All good",
        call_to_action=[],
        failure_message=None,
        created_at=now,
        completed_at=now,
        clauses=[clause],
    )
    data = review.model_dump()
    assert len(data["clauses"]) == 1
    assert data["clauses"][0]["section_number"] == "3.1"


def test_review_out_includes_failure_code():
    now = datetime.now(UTC)
    review = ReviewOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="failed",
        review_instructions=None,
        overall_fairness=None,
        summary=None,
        call_to_action=None,
        failure_message="Evaluation timed out",
        failure_code="timeout",
        created_at=now,
        completed_at=None,
    )
    data = review.model_dump()
    assert data["failure_code"] == "timeout"


def test_clause_out():
    clause = ClauseOut(
        id=uuid.uuid4(),
        section_number="2.1",
        clause_type="indemnification",
        purpose="Mutual indemnification",
        fairness="non-standard",
        market_standard="Typically mutual",
        explanation="One-sided indemnification favoring vendor.",
    )
    data = clause.model_dump()
    assert data["section_number"] == "2.1"
    assert data["clause_type"] == "indemnification"
    assert data["purpose"] == "Mutual indemnification"
    assert data["fairness"] == "non-standard"
    assert data["market_standard"] == "Typically mutual"
    assert data["explanation"] == "One-sided indemnification favoring vendor."


# --- Agentic pipeline schema tests ---


def test_review_out_includes_agreement_type():
    now = datetime.now(UTC)
    review = ReviewOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="completed",
        review_instructions=None,
        overall_fairness="fair",
        summary="Looks good",
        call_to_action=["Fix 3.1"],
        failure_message=None,
        created_at=now,
        completed_at=now,
        agreement_type="NDA",
    )
    data = review.model_dump()
    assert data["agreement_type"] == "NDA"


def test_review_out_agreement_type_default_none():
    now = datetime.now(UTC)
    review = ReviewOut(
        id=uuid.uuid4(),
        contract_id=uuid.uuid4(),
        status="pending",
        review_instructions=None,
        overall_fairness=None,
        summary=None,
        call_to_action=None,
        failure_message=None,
        created_at=now,
        completed_at=None,
    )
    data = review.model_dump()
    assert data["agreement_type"] is None


def test_clause_out_agentic_fields():
    clause = ClauseOut(
        id=uuid.uuid4(),
        section_number="4.1",
        clause_type="indemnification",
        purpose="Limits liability",
        fairness="non-standard",
        market_standard="Mutual indemnification",
        explanation="One-sided",
        status="evaluated",
        severity=3,
        playbook_status="flagged",
        playbook_position="Section 4",
        contract_language="Vendor shall...",
        finding="One-sided indemnification",
        recommended_redline="Add mutual language",
        relevant_checks=["check_1"],
        cross_references=["section_3"],
        is_cycle=True,
        is_synthetic=False,
    )
    data = clause.model_dump()
    assert data["status"] == "evaluated"
    assert data["severity"] == 3
    assert data["playbook_status"] == "flagged"
    assert data["playbook_position"] == "Section 4"
    assert data["contract_language"] == "Vendor shall..."
    assert data["finding"] == "One-sided indemnification"
    assert data["recommended_redline"] == "Add mutual language"
    assert data["relevant_checks"] == ["check_1"]
    assert data["cross_references"] == ["section_3"]
    assert data["is_cycle"] is True
    assert data["is_synthetic"] is False


def test_clause_out_agentic_fields_default_null():
    clause = ClauseOut(
        id=uuid.uuid4(),
        section_number="1.0",
        clause_type="termination",
    )
    data = clause.model_dump()
    assert data["status"] == "pending"
    assert data["severity"] is None
    assert data["playbook_status"] is None
    assert data["contract_language"] is None
    assert data["finding"] is None
    assert data["recommended_redline"] is None
    assert data["relevant_checks"] is None
    assert data["cross_references"] is None
    assert data["is_cycle"] is False
    assert data["is_synthetic"] is False
    assert data["purpose"] is None
    assert data["fairness"] is None
    assert data["market_standard"] is None
    assert data["explanation"] is None
