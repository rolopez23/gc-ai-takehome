import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    contract_id: uuid.UUID
    review_id: uuid.UUID
    status: str


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    upload_type: str
    created_at: datetime


class ContractListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    upload_type: str
    created_at: datetime
    review_status: str | None = None
    overall_fairness: str | None = None
    failure_code: str | None = None


class ContractDetailOut(ContractOut):
    text: str | None


class ClauseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_number: str
    clause_type: str
    purpose: str | None = None
    fairness: str | None = None
    market_standard: str | None = None
    explanation: str | None = None

    # Agentic pipeline fields
    status: str = "pending"
    severity: int | None = None
    playbook_status: str | None = None
    playbook_position: str | None = None
    contract_language: str | None = None
    finding: str | None = None
    recommended_redline: str | None = None
    relevant_checks: list | None = None
    cross_references: list | None = None
    is_cycle: bool = False
    is_synthetic: bool = False


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    status: str
    review_instructions: str | None
    overall_fairness: str | None
    summary: str | None
    call_to_action: list | None
    failure_message: str | None
    failure_code: str | None = None
    agreement_type: str | None = None
    created_at: datetime
    completed_at: datetime | None


class ReviewDetailOut(ReviewOut):
    clauses: list[ClauseOut]
