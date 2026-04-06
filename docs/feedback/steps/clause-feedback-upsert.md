# Step: clause-feedback-upsert

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

`PUT /api/reviews/clauses/{clause_id}/feedback` — creates or updates clause-level feedback.
Same upsert semantics as review feedback: omitted comment clears existing.

## Done When

- PUT with vote + comment creates a new clause feedback record
- PUT again overwrites and clears comment when not provided
- PUT on nonexistent clause_id returns 404
- Tests green

## Dependencies

- **feedback-schema** (models + schemas exist)

## Cycles

### upsert-create

**Test** — write in `backend/tests/test_feedback.py` and confirm it fails:
- **test_put_clause_feedback_create**: PUT `{"vote": "down", "comment": "wrong analysis"}` to
  `/api/reviews/clauses/{clause_id}/feedback`. Assert 200, response has correct fields.
  · setup: Contract + ContractReview + ReviewClause in db

**Code** — Add to `backend/routers/reviews.py`:
```python
from models import ClauseFeedback, ReviewClause as ReviewClauseModel
from schemas import ClauseFeedbackOut

@router.put("/clauses/{clause_id}/feedback", response_model=ClauseFeedbackOut)
async def upsert_clause_feedback(
    clause_id: uuid.UUID,
    body: FeedbackIn,
    db: AsyncSession = Depends(get_db),
):
    clause = await db.get(ReviewClauseModel, clause_id)
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    result = await db.execute(
        select(ClauseFeedback).where(ClauseFeedback.clause_id == clause_id)
    )
    feedback = result.scalar_one_or_none()
    if feedback:
        feedback.vote = body.vote
        feedback.comment = body.comment
    else:
        feedback = ClauseFeedback(
            clause_id=clause_id, vote=body.vote, comment=body.comment
        )
        db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback
```

**Refactor** — none

**Commit**: `add PUT /api/reviews/clauses/{clause_id}/feedback endpoint`

---

### upsert-update-clears-comment

**Test** — write and confirm it fails:
- **test_put_clause_feedback_update_clears_comment**: PUT with comment, then PUT without.
  Assert comment cleared. · setup: same

**Code** — Already handled by upsert logic. Test only.

**Refactor** — none

**Commit**: `add test for clause feedback vote change clearing comment`

---

### upsert-not-found

**Test** — write and confirm it fails:
- **test_put_clause_feedback_not_found**: PUT to nonexistent clause_id. Assert 404.

**Code** — Already handled. Test only.

**Refactor** — none

**Commit**: `add test for clause feedback 404 on missing clause`

---

## Verification

```bash
CLAUSE_ID="<clause-id>"

# Create
curl -s -X PUT http://localhost:8000/api/reviews/clauses/$CLAUSE_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote": "down", "comment": "incorrect"}' | python -m json.tool
# Expected: 200, vote=down, comment="incorrect"

# Update — clears comment
curl -s -X PUT http://localhost:8000/api/reviews/clauses/$CLAUSE_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote": "up"}' | python -m json.tool
# Expected: 200, vote=up, comment=null

# 404
curl -s -X PUT http://localhost:8000/api/reviews/clauses/00000000-0000-0000-0000-000000000000/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote": "up"}' -w "\n%{http_code}"
# Expected: 404
```
