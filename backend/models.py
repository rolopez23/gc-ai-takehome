import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    upload_type: Mapped[str] = mapped_column()
    original_blob: Mapped[bytes] = deferred(mapped_column(LargeBinary))
    pdf_blob: Mapped[bytes | None] = deferred(mapped_column(LargeBinary, nullable=True))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    reviews: Mapped[list["ContractReview"]] = relationship(back_populates="contract")


class ContractReview(Base):
    __tablename__ = "contract_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contracts.id"))
    status: Mapped[str] = mapped_column(default="pending")
    review_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_fairness: Mapped[str | None] = mapped_column(nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_to_action: Mapped[list | None] = mapped_column(JSON, nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agreement_type: Mapped[str | None] = mapped_column(nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="reviews")
    clauses: Mapped[list["ReviewClause"]] = relationship(back_populates="review")


class ReviewClause(Base):
    __tablename__ = "review_clauses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contract_reviews.id"))
    section_number: Mapped[str] = mapped_column()
    clause_type: Mapped[str] = mapped_column()
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    fairness: Mapped[str | None] = mapped_column(nullable=True)
    market_standard: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Agentic pipeline columns
    status: Mapped[str] = mapped_column(default="pending")
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    playbook_status: Mapped[str | None] = mapped_column(nullable=True)
    playbook_position: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_language: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_redline: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevant_checks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cross_references: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_cycle: Mapped[bool] = mapped_column(Boolean, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)

    review: Mapped["ContractReview"] = relationship(back_populates="clauses")
