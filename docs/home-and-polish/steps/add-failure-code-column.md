# Step: add-failure-code-column

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Adds a `failure_code` nullable string column to `ContractReview` and exposes it in the Pydantic response schemas. This gives the frontend a stable enum to map to user-friendly messages.

## Done When

1. `ContractReview.failure_code` column exists in model
2. `ReviewOut` includes `failure_code: str | None`
3. Alembic migration adds the column
4. Tests confirm the field roundtrips through ORM and schema

## Cycles

### model-and-schema

**Test** — write these tests and confirm they fail:
- **test_contract_review_has_failure_code**: Create a `ContractReview`, set `failure_code="timeout"`, commit, refresh, assert `failure_code == "timeout"` · setup: `db` fixture
- **test_review_out_includes_failure_code**: Construct `ReviewOut` from a dict with `failure_code="too_large"`, assert the field serializes · setup: none

**Code** —
- `models.py`: Add `failure_code: Mapped[str | None] = mapped_column(nullable=True)` to `ContractReview`
- `schemas.py`: Add `failure_code: str | None` to `ReviewOut`
- Create `backend/migrations/versions/002_add_failure_code.py`

**Refactor** — none

**Commit**: `add failure_code column to ContractReview model and schema`

---

## Verification

```bash
cd backend && uv run pytest tests/test_evaluation.py tests/test_schemas.py -v
cd backend && uv run alembic upgrade head
psql $DATABASE_URL -c "\d contract_reviews" | grep failure_code
# Expected: failure_code | character varying | nullable
```
