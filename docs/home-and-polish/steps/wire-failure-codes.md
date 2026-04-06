# Step: wire-failure-codes

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Sets the correct `failure_code` at every failure site in `evaluation.py` so each error type is deterministically tagged.

## Done When

Every `_fail_review` call passes a `failure_code` and tests confirm the correct code is set for each error scenario.

## Cycles

### fail-review-signature

**Test** — write these tests and confirm they fail:
- **test_run_eval_timeout_sets_failure_code**: `APITimeoutError` → `failure_code == "timeout"`
- **test_run_eval_api_error_sets_failure_code**: `APIError` → `failure_code == "anthropic_error"`
- **test_run_eval_max_tokens_sets_failure_code**: `max_tokens` → `failure_code == "too_large"`
- **test_run_eval_parse_failure_sets_failure_code**: garbage response → `failure_code == "parse_error"`
- **test_run_eval_unexpected_error_sets_failure_code**: generic `Exception` → `failure_code == "unknown"`

Setup: existing `_create_contract_and_review` helper + mock Anthropic patterns from `test_evaluation.py`.

**Code** — Update `_fail_review` to accept `failure_code: str` and set `review.failure_code = failure_code`. Update every call site:
- Line 113 (max_tokens): `"too_large"`
- Line 117 (empty response): `"anthropic_error"`
- Line 122 (wrong content type): `"anthropic_error"`
- Line 154 (parse error): `"parse_error"`
- Line 157 (APITimeoutError): `"timeout"`
- Line 159 (APIError): `"anthropic_error"`
- Line 161 (generic Exception): `"unknown"`
- Line 184 (pipeline error): `"unknown"`

**Refactor** — none

**Commit**: `wire failure_code to all _fail_review call sites`

---

## Verification

```bash
cd backend && uv run pytest tests/test_evaluation.py -v
# All 5 new failure_code tests pass + all existing tests still green
```
