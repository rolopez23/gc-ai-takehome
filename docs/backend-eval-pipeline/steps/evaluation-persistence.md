# Step 7: evaluation-persistence

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Sequential (after step 6)

## What This Step Delivers

`run_evaluation()` — the full orchestration function that calls Anthropic, parses the response,
and persists results to the database. Handles all three completion states + error conditions.
Status transitions are atomic within a DB session.

## Done When

- `run_evaluation(review_id, contract, db)` updates review to `completed` with fairness, summary, clauses
- Not-a-contract input: review `completed` with `overall_fairness=None`, summary from rejection
- API errors: review `failed` with descriptive `failure_message`
- Timeout (90s): review `failed` with timeout message
- `max_tokens` stop: review `failed` with "too large" message
- Parse errors: review `failed` with invalid response message
- Status set to `evaluating` at start of API call

## Cycles

### run-evaluation-success

**Test** — write these tests and confirm they fail:
- **test_run_eval_success**: Create contract (txt, with text) + pending review. Mock Anthropic to return EvalSuccess JSON. Call `run_evaluation`. Assert review: `status="completed"`, `overall_fairness="fair"`, `summary` set, `call_to_action` set, `completed_at` set. Assert 2 ReviewClause rows created. · setup: SQLite test DB, monkeypatched anthropic client

**Code** — Implement `async run_evaluation(review_id, contract, db)`:
1. Set `status="evaluating"`, flush
2. Build messages from contract's `pdf_blob`/`text` + review's `review_instructions`
3. Call `client.messages.create(..., timeout=90)`
4. Parse response
5. On success: set `overall_fairness`, `summary`, `call_to_action`, create `ReviewClause` rows, set `status="completed"`, `completed_at=now()`
6. Commit

**Refactor** — none

**Commit**: `Implement run_evaluation success path`

---

### run-evaluation-not-a-contract

**Test** — write these tests and confirm they fail:
- **test_run_eval_not_a_contract**: Mock Anthropic to return EvalError. Call `run_evaluation`. Assert `status="completed"`, `overall_fairness=None`, `summary` = rejection reason, no clauses.

**Code** — Add not-a-contract branch after parse.

**Refactor** — none

**Commit**: `Handle not-a-contract as completed with null fairness`

---

### run-evaluation-errors

**Test** — write these tests and confirm they fail:
- **test_run_eval_api_error**: Mock Anthropic to raise `APIError`. Assert `status="failed"`, `failure_message` set.
- **test_run_eval_timeout**: Mock to raise `APITimeoutError`. Assert `status="failed"`, message mentions timeout.
- **test_run_eval_max_tokens**: Mock response with `stop_reason="max_tokens"`. Assert `status="failed"`, message mentions "too large".
- **test_run_eval_parse_failure**: Mock response with garbage text. Assert `status="failed"`, message mentions invalid response.

**Code** — Wrap API call + parse in try/except. Catch `anthropic.APIError`, `anthropic.APITimeoutError`, general `Exception`. Check `stop_reason`. Set `status="failed"`, `failure_message`, `completed_at=now()`.

**Refactor** — none

**Commit**: `Handle API errors, timeouts, and parse failures in run_evaluation`

---

## Verification

```python
# Run tests and inspect DB state after mock evaluation:
# (This verification runs the test suite and prints row state)

import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# After running: pytest tests/test_evaluation.py -v
# Inspect that the test DB had correct rows created:

# The test_run_eval_success test should produce:
# - 1 ContractReview row: status=completed, overall_fairness set, summary set
# - N ReviewClause rows matching the mocked response clauses
# Evidence: pytest -v output showing all assertions passed

# Run:
# cd backend && uv run pytest tests/test_evaluation.py -v
# Expected: all tests pass, including:
#   test_run_eval_success PASSED
#   test_run_eval_not_a_contract PASSED
#   test_run_eval_api_error PASSED
#   test_run_eval_timeout PASSED
#   test_run_eval_max_tokens PASSED
#   test_run_eval_parse_failure PASSED
```
