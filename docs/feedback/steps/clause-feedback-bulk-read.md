# Step: clause-feedback-bulk-read

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

`GET /api/reviews/{review_id}/clause-feedback` — returns all clause feedback records for
clauses belonging to a given review. This is the bulk read the frontend uses on first hover.

## Done When

- GET returns list of clause feedback for the review's clauses
- GET returns empty list when no clause feedback exists
- GET returns 404 on nonexistent review_id
- Results are scoped — feedback from other reviews is not included
- Tests green

## Dependencies

- **clause-feedback-upsert** (PUT endpoint exists to create test data)

## Cycles

### bulk-read

**Test** — write in `backend/tests/test_feedback.py` and confirm it fails:
- **test_get_clause_feedback_all**: Create 2 clauses on a review, PUT feedback on both.
  GET `/api/reviews/{review_id}/clause-feedback`. Assert 200, list of 2 items with correct
  clause_ids. · setup: Contract + ContractReview + 2 ReviewClauses

**Code** — Add to `backend/routers/reviews.py`:
```python
@router.get("/{review_id}/clause-feedback", response_model=list[ClauseFeedbackOut])
async def get_clause_feedback(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    review = await db.get(ContractReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    result = await db.execute(
        select(ClauseFeedback)
        .join(ReviewClauseModel, ClauseFeedback.clause_id == ReviewClauseModel.id)
        .where(ReviewClauseModel.review_id == review_id)
    )
    return result.scalars().all()
```

**Refactor** — none

**Commit**: `add GET /api/reviews/{review_id}/clause-feedback bulk endpoint`

---

### bulk-read-empty

**Test** — write and confirm it fails:
- **test_get_clause_feedback_empty**: GET on review with clauses but no feedback. Assert 200,
  empty list. · setup: Contract + ContractReview + ReviewClause (no feedback)

**Code** — Already handled. Test only.

**Refactor** — none

**Commit**: `add test for empty clause feedback list`

---

### bulk-read-scoped

**Test** — write and confirm it fails:
- **test_get_clause_feedback_scoped**: Create 2 reviews, each with a clause. PUT feedback on
  both clauses. GET for review 1. Assert only review 1's clause feedback returned.

**Code** — Already handled by the join + where clause. Test only.

**Refactor** — none

**Commit**: `add test for clause feedback scoping to review`

---

### bulk-read-not-found

**Test** — write and confirm it fails:
- **test_get_clause_feedback_not_found**: GET on nonexistent review_id. Assert 404.

**Code** — Already handled. Test only.

**Refactor** — none

**Commit**: `add test for clause feedback bulk read 404`

---

## Verification

```bash
REVIEW_ID="<review-id>"

# After creating clause feedback in previous step
curl -s http://localhost:8000/api/reviews/$REVIEW_ID/clause-feedback | python -m json.tool
# Expected: 200, array of feedback objects scoped to this review

# 404
curl -s http://localhost:8000/api/reviews/00000000-0000-0000-0000-000000000000/clause-feedback -w "\n%{http_code}"
# Expected: 404
```
