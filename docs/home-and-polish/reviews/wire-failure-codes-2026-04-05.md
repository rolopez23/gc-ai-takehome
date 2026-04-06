## Review: wire-failure-codes
## Date: 2026-04-05

### Simplify findings

- **Keyword-only arg pattern**: `_fail_review(..., *, failure_code: str)` is clean -- forces callers to name the argument, preventing positional mistakes. Good.
- **No duplication in production code**: The failure_code is set in exactly one place (`_fail_review`), no scattered assignments.
- **Test duplication**: The 5 new failure_code tests duplicate the setup/mock pattern from the existing `test_run_eval_*` tests (timeout, api_error, max_tokens, parse_failure). The only new assertion is `review.failure_code == "..."`. This could be DRY'd with a parametrized test, but the current approach is readable and each test is self-contained. Not worth changing.
- **Diff is minimal**: 9 lines changed in evaluation.py (1 signature + 1 assignment + 7 call sites). Tight.

### Review findings

**All 8 call sites covered** -- confirmed by grep. Every `_fail_review` invocation has a `failure_code=` keyword.

**Code assignments are correct**:
- `too_large` for max_tokens -- correct, the contract exceeded token limit.
- `anthropic_error` for empty response, wrong content type, and APIError -- correct, all are API-side issues.
- `parse_error` for invalid/unparseable JSON -- correct.
- `timeout` for APITimeoutError -- correct.
- `unknown` for generic Exception and pipeline error -- correct catch-all.

**No enum, just string literals**: The failure codes are implicit (no Python enum or DB check constraint). This is fine for now -- there are only 5 distinct values and they are all co-located in one file. If codes proliferate or are consumed by frontend logic, an enum or Literal type would help. Low priority.

**Missing test coverage**:
- Lines 118 (empty response) and 123 (non-text content type) both set `anthropic_error` but have no dedicated failure_code test. They are partially covered by the existing tests that check `review.status == "failed"`, but the failure_code is not asserted for these two paths specifically. **Low risk** -- the `anthropic_error` code is tested via the APIError path, and the assignment is trivially correct by inspection.
- Line 185 (pipeline error in `evaluate_contract_task`) sets `unknown` but is not tested. This is the outer wrapper function. **Low risk** -- would require mocking `db.get` to fail inside the wrapper, which is awkward.

### Triage

| Finding | Severity | Action |
|---------|----------|--------|
| No enum/Literal for failure codes | Low | Note for future -- add if codes grow or frontend depends on exact values |
| Empty-response and non-text paths lack failure_code assertions | Low | Optional -- add if touching these tests later |
| Pipeline error path untested | Low | Optional -- awkward to test, low value |

### Verdict

Ship as-is. All findings are low severity and do not warrant blocking changes.
