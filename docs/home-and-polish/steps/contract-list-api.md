# Step: contract-list-api

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Extends `GET /api/contracts/` to return the latest review's status, overall_fairness, and failure_code per contract. The frontend dashboard depends on this data to render the contract list without making N+1 requests.

## Done When

1. `GET /api/contracts/` returns `ContractListOut[]` with `review_status`, `overall_fairness`, `failure_code`
2. When a contract has multiple reviews, only the latest (by `created_at`) is joined
3. When a contract has no reviews, the review fields are null
4. Existing `test_list_contracts_no_blobs` still passes (adapted to new schema)

## Cycles

### contract-list-out-schema

**Test** ��� write these tests and confirm they fail:
- **test_contract_list_out_schema**: Construct `ContractListOut` with all fields including `review_status="completed"`, `overall_fairness="fair"`, `failure_code=None`. Assert all fields serialize correctly. · setup: none (unit test)
- **test_contract_list_out_nullable_review_fields**: Construct `ContractListOut` with `review_status=None`, `overall_fairness=None`, `failure_code=None`. Assert fields are null. · setup: none

**Code** — Add `ContractListOut` to `schemas.py`:
```python
class ContractListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    upload_type: str
    created_at: datetime
    review_status: str | None = None
    overall_fairness: str | None = None
    failure_code: str | None = None
```

**Refactor** — none

**Commit**: `add ContractListOut schema with review fields`

---

### list-endpoint-joins-latest-review

**Test** — write these tests and confirm they fail:
- **test_list_contracts_includes_review_data**: Upload a contract, manually set its review to `status="completed"`, `overall_fairness="fair"`. Call `GET /api/contracts/`. Assert the first item has `review_status="completed"` and `overall_fairness="fair"`. · setup: `client` fixture
- **test_list_contracts_shows_latest_review**: Upload a contract, create a second review with different status. Call `GET /api/contracts/`. Assert the returned review data matches the latest review. · setup: `client` + `db` fixtures
- **test_list_contracts_no_review**: Insert a contract directly (no review). Call `GET /api/contracts/`. Assert `review_status` is null. · setup: `db` + `client` fixtures

**Code** — Rewrite `list_contracts` in `contracts.py` to use a subquery that selects the latest review per contract:
```python
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

@router.get("/", response_model=list[ContractListOut])
async def list_contracts(db: AsyncSession = Depends(get_db)):
    # Subquery: latest review_id per contract
    latest_review = (
        select(
            ContractReview.contract_id,
            func.max(ContractReview.created_at).label("max_created"),
        )
        .group_by(ContractReview.contract_id)
        .subquery()
    )

    stmt = (
        select(
            Contract.id,
            Contract.name,
            Contract.upload_type,
            Contract.created_at,
            ContractReview.status.label("review_status"),
            ContractReview.overall_fairness,
            ContractReview.failure_code,
        )
        .outerjoin(latest_review, Contract.id == latest_review.c.contract_id)
        .outerjoin(
            ContractReview,
            (ContractReview.contract_id == Contract.id)
            & (ContractReview.created_at == latest_review.c.max_created),
        )
        .order_by(Contract.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.mappings().all()
```

Update the import in `contracts.py` to include `ContractListOut` from `schemas`.

**Refactor** — Update existing `test_list_contracts_no_blobs` to also assert the new review fields are present.

**Commit**: `join latest review data into contract list endpoint`

---

## Verification

```bash
# 1. Run backend tests
cd backend && uv run pytest tests/test_contracts.py tests/test_schemas.py -v

# 2. Manual: upload a contract, then query list
curl -s localhost:8000/api/contracts/upload -F file=@test.txt | jq .
curl -s localhost:8000/api/contracts/ | jq '.[0] | {name, review_status, overall_fairness, failure_code}'
# Expected: review_status="pending" (or "completed" after eval finishes), overall_fairness, failure_code
```
