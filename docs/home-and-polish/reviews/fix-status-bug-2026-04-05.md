## Review: fix-status-bug
## Date: 2026-04-05

---

### Standard Review

Clean bill of health. Verified that `expire_on_commit=False` is set on both production and test session factories, so the early commit doesn't expire loaded objects. Error paths (`_fail_review`) already call `db.commit()`, so two commits in the happy path is consistent.

---

### Edge Case Hunter

- **evaluation.py:182-185** — If `db.commit()` on line 100 raises, the outer except on line 182 reuses the session without rollback. `db.get` would fail on the dirty session; review stuck in pre-commit state silently. fix: `await db.rollback()` before `db.get` in outer except · `[Valid — but pre-existing: the outer except had the same issue before this change if flush() failed. The commit() change doesn't introduce this; it just changes when it could trigger. Low priority.]`

---

### Adversarial

1. **evaluation.py:99** — No rollback on failure; status permanently "evaluating" if process crashes between commits · `[Dismissed: explicitly accepted in spec — "Stale evaluating status recovery sweep (accept risk for take-home scope)"]`
2. **evaluation.py:99** — Breaks transactional atomicity; mid-function commit splits one unit of work into two · `[Dismissed: intentional — the whole point is to make status visible to other sessions mid-operation]`
3. **test_evaluation.py** — Test doesn't verify the failure path after early commit · `[Speculative — existing failure tests (test_run_eval_api_error, test_run_eval_timeout, etc.) already verify status transitions to "failed". The early commit doesn't change that path.]`
4. **test_evaluation.py** — Test uses same session, doesn't prove cross-session visibility · `[Valid — the test verifies the commit() call happened by refreshing, but doesn't prove a separate connection sees it. However, this is an inherent limitation of SQLite test DB. The live verification (curl polling) proved cross-session visibility.]`
5. **evaluation.py** — Silent permanent stale status with no alerting · `[Dismissed: accepted risk per spec]`
6. **evaluation.py** — Race with concurrent callers calling run_evaluation twice for same review · `[Speculative — would require duplicate background task scheduling. FastAPI BackgroundTasks doesn't retry, and the upload endpoint creates one review per upload. Extremely unlikely.]`
7. **test_evaluation.py** — `captured_status` dict KeyError if mock not called · `[Dismissed: if mock wiring breaks, the test fails — that's correct behavior. A KeyError is a clear enough signal.]`
8. **test_evaluation.py** — No test for commit vs flush distinction · `[Dismissed: the test verifies the behavioral outcome (status visible after refresh), which is what matters. Testing internal method calls would be testing implementation.]`
9. **evaluation.py** — Assumes mid-function commit is safe for session lifecycle · `[Dismissed: run_evaluation is called from evaluate_contract_task which creates its own session via AsyncSessionLocal. No caller manages the transaction externally.]`
10. **evaluation.py** — No index on status column for polling queries · `[Speculative — polling queries filter by review_id (primary key), not by status. Not relevant to this diff.]`

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 0 | 0 | 0 | Useful — correctly confirmed safety via expire_on_commit check |
| Edge Case Hunter | 1 | 1 | 0 | Useful — found a real (pre-existing) session-state gap |
| Adversarial | 10 | 8 | 2 | Noisy — 9 of 10 dismissed or speculative, but forced thorough thinking |

**Notes:** The edge-case hunter's finding about the outer except not rolling back is valid but pre-existing — it existed before this change. Worth noting for a future hardening pass but not blocking for this step.
