## Verify: wire-failure-codes
## Date: 2026-04-05

### Tests

All 6 failure_code tests pass (includes 5 scenario tests + 1 model-level test):

```
tests/test_evaluation.py::test_contract_review_has_failure_code PASSED
tests/test_evaluation.py::test_run_eval_timeout_sets_failure_code PASSED
tests/test_evaluation.py::test_run_eval_api_error_sets_failure_code PASSED
tests/test_evaluation.py::test_run_eval_max_tokens_sets_failure_code PASSED
tests/test_evaluation.py::test_run_eval_parse_failure_sets_failure_code PASSED
tests/test_evaluation.py::test_run_eval_unexpected_error_sets_failure_code PASSED
```

### Call-site audit

All 8 `_fail_review` calls in `evaluation.py` pass a `failure_code=` keyword arg:

| Line | Scenario | Code |
|------|----------|------|
| 114 | max_tokens stop reason | `too_large` |
| 118 | Empty response | `anthropic_error` |
| 123 | Non-text content type | `anthropic_error` |
| 155 | Parse error (invalid JSON / wrong schema) | `parse_error` |
| 158 | APITimeoutError | `timeout` |
| 160 | APIError | `anthropic_error` |
| 162 | Generic Exception | `unknown` |
| 185 | Pipeline error (evaluate_contract_task) | `unknown` |

### DB check

Could not verify existing failed reviews in the DB (psql access denied from this session). Expected: pre-existing failed reviews would have `failure_code=null` since the column was added with nullable=True and no backfill migration.

### Schema & model

- `models.py`: `failure_code: Mapped[str | None] = mapped_column(nullable=True)` -- correct.
- `schemas.py`: `failure_code: str | None = None` exposed in both `ContractListItem` and `ReviewDetail` -- correct.
- Migration `002_add_failure_code.py` exists.

---
Overall: Verified
