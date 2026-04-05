"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("upload_type", sa.String(), nullable=False),
        sa.Column("original_blob", sa.LargeBinary(), nullable=False),
        sa.Column("pdf_blob", sa.LargeBinary(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "contract_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("contract_id", sa.Uuid(), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("review_instructions", sa.Text(), nullable=True),
        sa.Column("overall_fairness", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("call_to_action", sa.JSON(), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "review_clauses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("review_id", sa.Uuid(), sa.ForeignKey("contract_reviews.id"), nullable=False),
        sa.Column("section_number", sa.String(), nullable=False),
        sa.Column("clause_type", sa.String(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("fairness", sa.String(), nullable=False),
        sa.Column("market_standard", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("review_clauses")
    op.drop_table("contract_reviews")
    op.drop_table("contracts")
