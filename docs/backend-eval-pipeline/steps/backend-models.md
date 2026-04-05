# Step 1: backend-models

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B1 (parallel with step 4)

## What This Step Delivers

New SQLAlchemy models that match the spec's database schema. Contract with blob storage,
ContractReview with completion states and review_instructions, ReviewClause replacing
ReviewResult. After this step, the data layer is ready for schemas and migration.

## Done When

- `Contract`, `ContractReview`, `ReviewClause` models create rows and query back correctly
- Blob columns (`original_blob`, `pdf_blob`) use deferred loading
- All three completion states representable (success, not-a-contract, failed)
- Old `ReviewResult` model removed

## Cycles

### contract-model

**Test** — write these tests and confirm they fail:
- **test_create_contract_with_blobs**: Create Contract with `name="test.pdf"`, `upload_type="pdf"`, `original_blob=b"fake-pdf"`, `pdf_blob=b"fake-pdf"`, `text=None`. Assert all fields round-trip.
- **test_contract_txt_has_text_no_pdf_blob**: Create Contract with `upload_type="txt"`, `text="hello"`, `pdf_blob=None`. Assert `text=="hello"` and `pdf_blob is None`.

**Code** — Rewrite `Contract` in `backend/models.py`: drop `vendor`, `customer`, `agreement_type`. Add `upload_type` (str), `original_blob` (LargeBinary, deferred), `pdf_blob` (LargeBinary, nullable, deferred). Keep `name`, `text` (nullable), `id`, `created_at`.

**Refactor** — none

**Commit**: `Rewrite Contract model with blob storage and upload_type`

---

### contract-review-model

**Test** — write these tests and confirm they fail:
- **test_create_review_pending**: Create ContractReview with `status="pending"`. Assert defaults: `overall_fairness=None`, `summary=None`, `call_to_action=None`, `failure_message=None`, `completed_at=None`, `review_instructions=None`.
- **test_review_completed_success**: Set `status="completed"`, `overall_fairness="dealbreaker"`, `summary="1 dealbreaker"`, `call_to_action=["Fix section 3"]`. Assert all fields.
- **test_review_completed_not_a_contract**: Set `status="completed"`, `overall_fairness=None`, `summary="Not a contract."`. Assert `overall_fairness is None`.
- **test_review_failed**: Set `status="failed"`, `failure_message="API timeout"`. Assert `failure_message` set.
- **test_review_instructions**: Create with `review_instructions="Focus on IP"`. Assert round-trip.

**Code** — Rewrite `ContractReview`: drop `meta`, `priority_issues`. Add `review_instructions` (Text, nullable), `overall_fairness` (str, nullable), `call_to_action` (JSON, nullable), `failure_message` (Text, nullable).

**Refactor** — none

**Commit**: `Rewrite ContractReview with completion states and review_instructions`

---

### review-clause-model

**Test** — write these tests and confirm they fail:
- **test_create_review_clause**: Create ReviewClause with all 6 fields. Assert round-trip.
- **test_clause_relationship**: Create ContractReview + 2 ReviewClauses. Load with `selectinload(ContractReview.clauses)`. Assert `len == 2`.

**Code** — Replace `ReviewResult` with `ReviewClause`. Fields: `id`, `review_id` (FK), `section_number`, `clause_type`, `purpose`, `fairness`, `market_standard`, `explanation`. Rename relationship on ContractReview from `results` to `clauses`.

**Refactor** — none

**Commit**: `Replace ReviewResult with ReviewClause`

---

## Verification

Insert a Contract, ContractReview (completed with fairness), and 2 ReviewClauses via the test
DB. Query back with relationship loading. Assert all fields match. This is covered by the
test suite — no external surface to verify beyond that.
