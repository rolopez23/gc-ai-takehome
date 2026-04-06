# Step: review-feedback-upsert

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

`PUT /api/reviews/{review_id}/feedback` — creates or updates review-level feedback. Omitted
or null comment clears any existing comment, ensuring vote changes don't leave stale text.

## Done When

- PUT with vote + comment creates a new feedback record and returns it
- PUT again with different vote overwrites and clears comment when not provided
- PUT on nonexistent review_id returns 404
- Tests green

## Dependencies

- **feedback-schema** (models + schemas exist)

## Cycles

### upsert-create

**Test** — write in `backend/tests/test_feedback.py` and confirm it fails:
- **test_put_review_feedback_create**: PUT `{"vote": "up", "comment": "good"}` to
  `/api/reviews/{review_id}/feedback`. Assert 200, response body has `vote="up"`,
  `comment="good"`, valid `id`, `review_id`, `created_at`, `updated_at`.
  · setup: Contract + ContractReview in db

**Code** — Add to `backend/routers/reviews.py`:
```python
from models import ReviewFeedback
from schemas import FeedbackIn, ReviewFeedbackOut

@router.put("/{review_id}/feedback", response_model=ReviewFeedbackOut)
async def upsert_review_feedback(
    review_id: uuid.UUID,
    body: FeedbackIn,
    db: AsyncSession = Depends(get_db),
):
    review = await db.get(ContractReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    result = await db.execute(
        select(ReviewFeedback).where(ReviewFeedback.review_id == review_id)
    )
    feedback = result.scalar_one_or_none()
    if feedback:
        feedback.vote = body.vote
        feedback.comment = body.comment
    else:
        feedback = ReviewFeedback(
            review_id=review_id, vote=body.vote, comment=body.comment
        )
        db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback
```

**Refactor** — none

**Commit**: `add PUT /api/reviews/{review_id}/feedback endpoint`

---

### upsert-update-clears-comment

**Test** — write and confirm it fails:
- **test_put_review_feedback_update_clears_comment**: PUT with `vote="up", comment="good"`,
  then PUT with `vote="down"` (no comment key). Assert second response has `vote="down"`,
  `comment=None`. · setup: same

**Code** — Already handled by the upsert logic above (`body.comment` defaults to `None` in
`FeedbackIn`, so omitting it sets comment to null). No new production code needed — this
cycle just adds the test.

**Refactor** — none

**Commit**: `add test for review feedback vote change clearing comment`

---

### upsert-not-found

**Test** — write and confirm it fails:
- **test_put_review_feedback_not_found**: PUT to `/api/reviews/{random_uuid}/feedback`.
  Assert 404.

**Code** — Already handled by the review existence check. No new production code.

**Refactor** — none

**Commit**: `add test for review feedback 404 on missing review`

---

## Verification

```bash
cd backend
uvicorn main:app --reload &

# Use an existing review_id or create one via upload
REVIEW_ID="<review-id>"

# Create
curl -s -X PUT http://localhost:8000/api/reviews/$REVIEW_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote": "up", "comment": "looks good"}' | python -m json.tool
# Expected: 200, vote=up, comment="looks good"

# Update — comment clears
curl -s -X PUT http://localhost:8000/api/reviews/$REVIEW_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote": "down"}' | python -m json.tool
# Expected: 200, vote=down, comment=null

# 404
curl -s -X PUT http://localhost:8000/api/reviews/00000000-0000-0000-0000-000000000000/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote": "up"}' -w "\n%{http_code}"
# Expected: 404
```
