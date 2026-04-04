import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# --- Contract ---

class ContractCreate(BaseModel):
    name: str
    vendor: str | None = None
    customer: str | None = None
    agreement_type: str | None = None
    text: str


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    vendor: str | None
    customer: str | None
    agreement_type: str | None
    created_at: datetime


class ContractDetailOut(ContractOut):
    text: str


# --- Review Result ---

class ReviewResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    check_number: int
    check_name: str
    importance: str
    status: str
    severity: int | None
    contract_language: str | None
    playbook_position: str
    finding: str
    recommended_redline: str | None


# --- Contract Review ---

class ContractReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    status: str
    summary: str | None
    meta: dict | None
    priority_issues: list | None
    created_at: datetime
    completed_at: datetime | None


class ContractReviewDetailOut(ContractReviewOut):
    results: list[ReviewResultOut]
