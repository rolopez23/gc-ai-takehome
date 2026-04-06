"""agentic pipeline columns

Revision ID: 003
Revises: 002
Create Date: 2026-04-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ContractReview: add agreement_type
    op.add_column(
        "contract_reviews", sa.Column("agreement_type", sa.String(), nullable=True)
    )

    # ReviewClause: make existing required fields nullable (clauses inserted at split time before eval)
    op.alter_column("review_clauses", "purpose", existing_type=sa.Text(), nullable=True)
    op.alter_column(
        "review_clauses", "fairness", existing_type=sa.String(), nullable=True
    )
    op.alter_column(
        "review_clauses", "market_standard", existing_type=sa.Text(), nullable=True
    )
    op.alter_column(
        "review_clauses", "explanation", existing_type=sa.Text(), nullable=True
    )

    # ReviewClause: add agentic pipeline columns
    op.add_column(
        "review_clauses",
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
    )
    op.add_column("review_clauses", sa.Column("severity", sa.Integer(), nullable=True))
    op.add_column(
        "review_clauses", sa.Column("playbook_status", sa.String(), nullable=True)
    )
    op.add_column(
        "review_clauses", sa.Column("playbook_position", sa.Text(), nullable=True)
    )
    op.add_column(
        "review_clauses", sa.Column("contract_language", sa.Text(), nullable=True)
    )
    op.add_column("review_clauses", sa.Column("finding", sa.Text(), nullable=True))
    op.add_column(
        "review_clauses", sa.Column("recommended_redline", sa.Text(), nullable=True)
    )
    op.add_column(
        "review_clauses", sa.Column("relevant_checks", sa.JSON(), nullable=True)
    )
    op.add_column(
        "review_clauses", sa.Column("cross_references", sa.JSON(), nullable=True)
    )
    op.add_column(
        "review_clauses",
        sa.Column(
            "is_cycle", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column(
        "review_clauses",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("review_clauses", "is_synthetic")
    op.drop_column("review_clauses", "is_cycle")
    op.drop_column("review_clauses", "cross_references")
    op.drop_column("review_clauses", "relevant_checks")
    op.drop_column("review_clauses", "recommended_redline")
    op.drop_column("review_clauses", "finding")
    op.drop_column("review_clauses", "contract_language")
    op.drop_column("review_clauses", "playbook_position")
    op.drop_column("review_clauses", "playbook_status")
    op.drop_column("review_clauses", "severity")
    op.drop_column("review_clauses", "status")

    op.alter_column(
        "review_clauses", "explanation", existing_type=sa.Text(), nullable=False
    )
    op.alter_column(
        "review_clauses", "market_standard", existing_type=sa.Text(), nullable=False
    )
    op.alter_column(
        "review_clauses", "fairness", existing_type=sa.String(), nullable=False
    )
    op.alter_column(
        "review_clauses", "purpose", existing_type=sa.Text(), nullable=False
    )

    op.drop_column("contract_reviews", "agreement_type")
