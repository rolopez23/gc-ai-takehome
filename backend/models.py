import uuid
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.types import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    vendor: Mapped[str | None] = mapped_column()
    customer: Mapped[str | None] = mapped_column()
    agreement_type: Mapped[str | None] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    reviews: Mapped[list["ContractReview"]] = relationship(back_populates="contract")


class ContractReview(Base):
    __tablename__ = "contract_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contracts.id"))
    status: Mapped[str] = mapped_column(default="pending")  # pending | running | completed | failed
    summary: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    priority_issues: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column()

    contract: Mapped["Contract"] = relationship(back_populates="reviews")
    results: Mapped[list["ReviewResult"]] = relationship(back_populates="review")


class ReviewResult(Base):
    __tablename__ = "review_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contract_reviews.id"))
    check_number: Mapped[int] = mapped_column()
    check_name: Mapped[str] = mapped_column()
    importance: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()  # TRIGGERED | PASS | ABSENT | PARTIAL
    severity: Mapped[int | None] = mapped_column()
    contract_language: Mapped[str | None] = mapped_column(Text)
    playbook_position: Mapped[str] = mapped_column(Text)
    finding: Mapped[str] = mapped_column(Text)
    recommended_redline: Mapped[str | None] = mapped_column(Text)

    review: Mapped["ContractReview"] = relationship(back_populates="results")
