# Review: m3-backend-eval-pipeline
## Date: 2026-04-05

---

### Standard Review

#### Edge Cases
- **conversion.py:78** — TXT upload with non-UTF-8 encoding (Latin-1, Windows-1252) causes `UnicodeDecodeError`, surfaces as unhandled 500 instead of 400. · `[Valid]`
- **evaluation.py:112** — `message.content[0]` on empty content list causes `IndexError` before the `not content` guard runs. · `[Valid]`

#### Contract Violations
- **types.ts:38-42** — `ReviewFailedSchema` omits `contract_id` unlike other response schemas. Backend always returns it. · `[Speculative — no current code needs contract_id from a failed response]`
- **models.py:34** — `call_to_action` typed as `Mapped[dict | None]` but stores `list[str]`. · `[Valid — type hint is wrong]`

---

### Edge Case Hunter

- **evaluation.py:112** — Anthropic returns empty content → IndexError before guard · fix: check `len(message.content) == 0` before indexing · `[Valid]`
- **conversion.py:78** — Non-UTF-8 .txt file → UnicodeDecodeError → 500 · fix: catch UnicodeDecodeError or use errors="replace" · `[Valid]`
- **contract/[id]/page.tsx:114-148** — Infinite polling loop with no timeout · fix: add POLL_TIMEOUT · `[Valid]`
- **contracts.py:74-84** — Multiple reviews per contract → `MultipleResultsFound` → 500 · fix: use `.first()` instead of `scalar_one_or_none` · `[Speculative — M3 is 1:1, but defensive fix is cheap]`
- **types.ts:38-41** — Backend failure_message can be null, Zod requires string · `[Valid — mismatch]`
- **contract/[id]/page.tsx:154** — `overall_fairness` truthiness check fails on empty string · `[Dismissed — empty string is not a valid fairness value]`

---

### Adversarial

1. **evaluation.py:94** — `reading` status never set (spec requires it) · `[Dismissed — spec says "statuses may be skipped if a phase is trivial" and conversion now happens at upload time, not in background]`
2. **evaluation.py:161** — `text` not undeferred, works because `text` isn't deferred in model · `[Dismissed — correct, text is NOT deferred]`
3. **conversion.py:76** — UTF-8 decode with no error handling · `[Valid — duplicate of standard #1]`
4. **evaluation.py:93-95** — `run_evaluation` doesn't null-check review · `[Valid — defensive fix]`
5. **contracts.py:26-27** — Reads entire file into memory before size check · `[Speculative — FastAPI's UploadFile has a configurable spool limit, but worth noting]`
6. **evaluation.py:112-113** — Empty content array IndexError · `[Valid — duplicate of standard #2]`
7. **conversion.py:37-39** — `_find_libreoffice` not cached · `[Speculative — minor, but easy to fix]`
8. **evaluation.py:16-18** — Env vars read at import time, `int()` can crash · `[Speculative — startup crash is acceptable for invalid config]`
9. **contract/[id]/page.tsx:116** — No polling timeout · `[Valid — duplicate of edge case #3]`
10. **contract/[id]/page.tsx:135-139** — Network errors show "not found" instead of retry/error · `[Valid]`
11. **models.py:34** — `dict | None` type hint wrong for list · `[Valid — duplicate of standard contract #2]`
12. **prompt.py** — Instructions injected unsanitized · `[Dismissed — user-provided input to their own evaluation, not a security issue]`
13. **evaluation.py:173-177** — Cascading DB failure in exception handler · `[Speculative — edge case of an edge case]`
14. **contracts.py:76-82** — MultipleResultsFound risk · `[Speculative — duplicate of edge case #4]`
15. **types.ts:39-42** — ReviewFailedSchema omits contract_id · `[Speculative — duplicate]`

---

## Fixes Applied

1. **conversion.py** — Catch `UnicodeDecodeError` on TXT decode, raise `ValueError`
2. **evaluation.py** — Check `message.content` length before indexing
3. **evaluation.py** — Null-check review in `run_evaluation`
4. **evaluation.py** — Cache `_find_libreoffice` with `@lru_cache`
5. **models.py** — Fix `call_to_action` type hint to `list | None`
6. **contract/[id]/page.tsx** — Add POLL_TIMEOUT to results page polling
7. **contract/[id]/page.tsx** — Show "connection error" on fetch failure instead of "not found"
8. **types.ts** — Make `failure_message` nullable in `ReviewFailedSchema`
9. **contracts.py** — Use `.first()` instead of `scalar_one_or_none()` for review-by-contract

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 4 | 2 | 2 | Useful — caught the encoding and type hint bugs clearly |
| Edge Case Hunter | 6 | 2 | 4 | Useful — found the infinite poll and MultipleResultsFound |
| Adversarial | 15 | 3 | 12 | Useful — network error UX and null-check were unique finds |

**Notes:** All three converged on the UTF-8 and empty content bugs. Adversarial's prompt injection concern is a design choice, not a bug. Edge case hunter's infinite poll was the highest-impact unique find.
