# Step: schema-migration

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

An Alembic migration that adds new columns to `ContractReview` and `ReviewClause`, updated ORM
models, and updated Pydantic schemas. The status state machine on `ContractReview` is expanded
to support the new pipeline states.

## Done When

- Migration `002_agentic_pipeline.py` runs cleanly on the dev database
- `ContractReview` has `agreement_type` column
- `ContractReview.status` supports: pending, verifying, splitting, evaluating, completed, failed, rejected
- `ReviewClause` has all new columns (status, severity, playbook fields, cross-reference fields, is_cycle, is_synthetic)
- ORM models and Pydantic schemas reflect the new columns
- Existing tests still pass (new columns are nullable, so backward compatible)

## Cycles

### alembic-migration

**Test** — write these tests and confirm they fail:
- **test_review_clause_has_status_column**: create a `ReviewClause` with `status="pending"`,
  persist, reload, assert status == "pending"
- **test_review_clause_has_severity_column**: create a `ReviewClause` with `severity=7`,
  persist, reload, assert severity == 7
- **test_review_clause_has_playbook_fields**: create a `ReviewClause` with
  `playbook_status="TRIGGERED"`, `playbook_position="Net 45"`, persist, assert values match
- **test_contract_review_has_agreement_type**: create a `ContractReview` with
  `agreement_type="SaaS MSA"`, persist, assert value matches
- **test_contract_review_rejected_status**: create a `ContractReview` with
  `status="rejected"`, persist, assert status == "rejected"

**Code** — create `backend/migrations/versions/002_agentic_pipeline.py`:

```python
# Add to contract_reviews:
op.add_column("contract_reviews", sa.Column("agreement_type", sa.String(), nullable=True))

# Add to review_clauses:
op.add_column("review_clauses", sa.Column("status", sa.String(), nullable=False, server_default="pending"))
op.add_column("review_clauses", sa.Column("severity", sa.Integer(), nullable=True))
op.add_column("review_clauses", sa.Column("playbook_status", sa.String(), nullable=True))
op.add_column("review_clauses", sa.Column("playbook_position", sa.Text(), nullable=True))
op.add_column("review_clauses", sa.Column("contract_language", sa.Text(), nullable=True))
op.add_column("review_clauses", sa.Column("finding", sa.Text(), nullable=True))
op.add_column("review_clauses", sa.Column("recommended_redline", sa.Text(), nullable=True))
op.add_column("review_clauses", sa.Column("relevant_checks", sa.JSON(), nullable=True))
op.add_column("review_clauses", sa.Column("cross_references", sa.JSON(), nullable=True))
op.add_column("review_clauses", sa.Column("is_cycle", sa.Boolean(), nullable=False, server_default=sa.text("false")))
op.add_column("review_clauses", sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.text("false")))
```

Update `backend/models.py` to add corresponding mapped columns. Make existing required fields
(`purpose`, `fairness`, `market_standard`, `explanation`) nullable since clauses are now
inserted at split time with null evaluation fields.

**Refactor** — none

**Commit**: `add migration 002 for agentic pipeline schema changes`

---

### update-pydantic-schemas

**Test** — write these tests and confirm they fail:
- **test_clause_out_includes_severity**: `ClauseOut` model accepts and serializes `severity=7`
- **test_clause_out_includes_playbook_status**: `ClauseOut` accepts `playbook_status="TRIGGERED"`
- **test_review_out_includes_agreement_type**: `ReviewOut` accepts `agreement_type="SaaS MSA"`
- **test_clause_out_nullable_eval_fields**: `ClauseOut` accepts `purpose=None` (for pending clauses)

**Code** — update `backend/schemas.py`:
- Add new fields to `ClauseOut` (all nullable)
- Add `agreement_type` to `ReviewOut`

**Refactor** — none

**Commit**: `update Pydantic schemas for agentic pipeline fields`

---

## Verification

```bash
# Run migration on dev database
cd backend && uv run alembic upgrade head

# Verify columns exist
docker exec -i $(docker ps -q -f name=postgres) psql -U app -d app -c "\d review_clauses"
docker exec -i $(docker ps -q -f name=postgres) psql -U app -d app -c "\d contract_reviews"
```

Expected: `review_clauses` shows all new columns (status, severity, playbook_status, etc.).
`contract_reviews` shows `agreement_type` column.

```bash
cd backend && uv run pytest -v
```

Expected: all existing tests still pass (backward compatible).
