# Step 2: pydantic-and-migration

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Sequential (after Batch 1)

## What This Step Delivers

Pydantic schemas for all API responses + fresh Alembic migration. Destructive reset of any
existing tables. After this step, the API layer has typed request/response models and the
database has the correct table structure.

## Done When

- Pydantic schemas serialize all three completion states correctly
- `UploadResponse`, `ContractOut`, `ReviewOut`, `ReviewDetailOut`, `ClauseOut` all validate
- `alembic upgrade head` creates `contracts`, `contract_reviews`, `review_clauses` tables
- `review_results` table no longer exists
- `make reset-db` target works for destructive reset

## Cycles

### pydantic-schemas

**Test** — write these tests and confirm they fail:
- **test_upload_response**: `UploadResponse(contract_id=uuid4(), review_id=uuid4(), status="pending")` serializes to dict with string UUIDs.
- **test_contract_out_excludes_blobs**: `ContractOut.model_fields` does NOT contain `original_blob` or `pdf_blob`.
- **test_review_out_completed**: `ReviewOut` with `status="completed"`, `overall_fairness="fair"`, `call_to_action=["Fix 3.1"]` serializes correctly.
- **test_review_out_rejected**: `ReviewOut` with `status="completed"`, `overall_fairness=None` serializes with `overall_fairness: null`.
- **test_review_out_failed**: `ReviewOut` with `status="failed"`, `failure_message="timeout"` serializes correctly.
- **test_review_detail_with_clauses**: `ReviewDetailOut` with `clauses=[ClauseOut(...)]` serializes nested list.
- **test_clause_out**: All 6 fields serialize.

**Code** — Rewrite `backend/schemas.py`:
- `UploadResponse`: `contract_id: UUID`, `review_id: UUID`, `status: str`
- `ContractOut`: `id`, `name`, `upload_type`, `created_at` (from_attributes=True)
- `ContractDetailOut(ContractOut)`: + `text: str | None`
- `ClauseOut`: `id: UUID`, `section_number`, `clause_type`, `purpose`, `fairness`, `market_standard`, `explanation`
- `ReviewOut`: `id`, `contract_id`, `status`, `review_instructions`, `overall_fairness`, `summary`, `call_to_action`, `failure_message`, `created_at`, `completed_at`
- `ReviewDetailOut(ReviewOut)`: + `clauses: list[ClauseOut]`

**Refactor** — none

**Commit**: `Rewrite Pydantic schemas for M3 API responses`

---

### alembic-migration

**Test** — write these tests and confirm they fail:
- **test_migration_creates_tables**: After `upgrade head` on test DB, inspect metadata. Assert `contracts`, `contract_reviews`, `review_clauses` exist. Assert `review_results` does NOT exist.

**Code** — Delete existing migration versions (if any). Generate fresh migration: `alembic revision --autogenerate -m "m3 initial schema"`. Verify the generated migration. Add to `Makefile`:
```makefile
reset-db:
	docker compose -f ../docker-compose.yml down -v
	docker compose -f ../docker-compose.yml up -d db
	sleep 2
	uv run alembic upgrade head
```

Update `backend/pyproject.toml` to add `python-multipart` and `anthropic` dependencies.

**Refactor** — none

**Commit**: `Fresh Alembic migration for M3 schema`

---

## Verification

```bash
cd backend
make reset-db

# Connect to DB and inspect:
docker compose -f ../docker-compose.yml exec db psql -U app -d app -c "\dt"
# Expected: contracts, contract_reviews, review_clauses (NO review_results)

docker compose -f ../docker-compose.yml exec db psql -U app -d app -c "\d contracts"
# Expected: id (uuid), name (varchar), upload_type (varchar), original_blob (bytea),
#           pdf_blob (bytea), text (text), created_at (timestamp)

docker compose -f ../docker-compose.yml exec db psql -U app -d app -c "\d contract_reviews"
# Expected: id, contract_id, status, review_instructions, overall_fairness,
#           summary, call_to_action (json), failure_message, created_at, completed_at
```
