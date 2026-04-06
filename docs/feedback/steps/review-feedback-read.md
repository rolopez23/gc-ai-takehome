# Step: review-feedback-read

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

`GET /api/reviews/{review_id}/feedback` — returns the review-level feedback record or null.

## Done When

- GET returns saved feedback after a PUT
- GET returns null (200) when no feedback exists
- GET returns 404 on nonexistent review_id
- Tests green

## Dependencies

- **review-feedback-upsert** (PUT endpoint exists to create test data)

## Cycles

### read-exists

**Test** — write in `backend/tests/test_feedback.py` and confirm it fails:
- **test_get_review_feedback_exists**: PUT feedback, then GET `/api/reviews/{review_id}/feedback`.
  Assert 200, response matches what was PUT. · setup: Contract + ContractReview in db

**Code** — Add to `backend/routers/reviews.py`:
```python
@router.get("/{review_id}/feedback", response_model=ReviewFeedbackOut | None)
async def get_review_feedback(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    review = await db.get(ContractReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    result = await db.execute(
        select(ReviewFeedback).where(ReviewFeedback.review_id == review_id)
    )
    return result.scalar_one_or_none()
```

**Refactor** — none

**Commit**: `add GET /api/reviews/{review_id}/feedback endpoint`

---

### read-none

**Test** — write and confirm it fails:
- **test_get_review_feedback_none**: GET on review with no feedback. Assert 200, response is `null`.

**Code** — Already handled. No new production code.

**Refactor** — none

**Commit**: `add test for GET review feedback returning null`

---

### read-not-found

**Test** — write and confirm it fails:
- **test_get_review_feedback_not_found**: GET on nonexistent review_id. Assert 404.

**Code** — Already handled. No new production code.

**Refactor** — none

**Commit**: `add test for GET review feedback 404`

---

## Verification

```bash
REVIEW_ID="<review-id>"

# After previous step's PUT, read it back
curl -s http://localhost:8000/api/reviews/$REVIEW_ID/feedback | python -m json.tool
# Expected: 200, feedback object

# Read on review with no feedback (use a different review)
curl -s http://localhost:8000/api/reviews/$OTHER_REVIEW_ID/feedback
# Expected: 200, null

# 404
curl -s http://localhost:8000/api/reviews/00000000-0000-0000-0000-000000000000/feedback -w "\n%{http_code}"
# Expected: 404
```
