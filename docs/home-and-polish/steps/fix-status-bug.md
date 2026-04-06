# Step: fix-status-bug

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Fixes the bug where polling always shows "pending". The "evaluating" status is flushed but never committed, so other sessions can't see it.

## Done When

`evaluation.py:99` uses `commit()` and a fresh DB session can see `status == "evaluating"` before the LLM call completes.

## Cycles

### commit-evaluating-status

**Test** — write these tests and confirm they fail:
- **test_run_eval_status_committed_before_api_call**: Run `run_evaluation` with a mocked Anthropic client. Inside the mock, query the review from a **fresh session** and assert `status == "evaluating"`. · setup: `db` fixture, mock Anthropic that checks DB mid-call

**Code** — In `evaluation.py:99`, change `await db.flush()` to `await db.commit()`.

**Refactor** — none

**Commit**: `fix status bug: commit evaluating status so polling sessions see it`

---

## Verification

```bash
cd backend && uv run pytest tests/test_evaluation.py::test_run_eval_status_committed_before_api_call -v

# Manual: upload a contract and poll rapidly — should see "evaluating" before "completed"
curl -s localhost:8000/api/contracts/upload -F file=@test.txt | jq .review_id
# Then poll: curl -s localhost:8000/api/reviews/{id} | jq .status
```
