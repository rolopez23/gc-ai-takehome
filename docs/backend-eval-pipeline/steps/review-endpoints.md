# Step 10: review-endpoints

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B2 (parallel)

## What This Step Delivers

`GET /api/reviews/{review_id}` returning correct shape for all states.
`GET /api/contracts/{contract_id}/review` returning the single review for a contract (1:1 M3
convenience endpoint). Old `create_review` and `list_reviews_for_contract` endpoints removed.

## Done When

- GET review by ID returns correct shape for pending, completed (success), completed (rejected), failed
- GET review by contract_id returns the same review
- Completed reviews include nested clauses
- 404 for nonexistent reviews or contracts

## Cycles

### get-review-by-id

**Test** — write these tests and confirm they fail:
- **test_get_review_pending**: Create pending review in DB. GET `/api/reviews/{id}`. Assert `status="pending"`, no clauses in response.
- **test_get_review_completed**: Create completed review + 2 clauses. GET. Assert `overall_fairness`, `summary`, `call_to_action`, `clauses` array with 2 items.
- **test_get_review_rejected**: Create completed review with `overall_fairness=None`. GET. Assert `overall_fairness` is null, `clauses` is empty.
- **test_get_review_failed**: Create failed review. GET. Assert `failure_message` present.
- **test_get_review_not_found**: GET nonexistent UUID. Assert 404.

**Code** — Rewrite `GET /api/reviews/{review_id}` in `backend/routers/reviews.py`. Load review with `selectinload(ContractReview.clauses)`. Return `ReviewDetailOut`. Remove `create_review` and `list_reviews_for_contract` endpoints.

**Refactor** — none

**Commit**: `Rewrite GET review endpoint with all completion states`

---

### get-review-by-contract

**Test** — write these tests and confirm they fail:
- **test_get_review_by_contract_id**: Create contract + review. GET `/api/contracts/{contract_id}/review`. Assert returns the review with matching `contract_id`.
- **test_get_review_by_contract_not_found**: GET with nonexistent contract. Assert 404.

**Code** — Add `GET /api/contracts/{contract_id}/review` to `reviews.py` (or `contracts.py`). Query `ContractReview` by `contract_id` with `selectinload`. Return `ReviewDetailOut`.

**Refactor** — none

**Commit**: `Add GET review by contract_id`

---

## Verification

```bash
cd backend && make dev

# After uploading a contract (from step 8):
# Get review by ID:
curl -s http://localhost:8000/api/reviews/{review_id} | python -m json.tool
# Expected: {"id": "...", "contract_id": "...", "status": "pending", ...}

# Get review by contract ID:
curl -s http://localhost:8000/api/contracts/{contract_id}/review | python -m json.tool
# Expected: same review

# To test completed state, manually update in DB:
# docker compose exec db psql -U app -d app -c "
#   UPDATE contract_reviews SET status='completed', overall_fairness='fair',
#   summary='Looks good', call_to_action='[\"No action needed\"]'
#   WHERE id='{review_id}';"
# Then curl again — assert completed shape with fairness.

# 404:
curl -s http://localhost:8000/api/reviews/00000000-0000-0000-0000-000000000000
# Expected: 404
```
