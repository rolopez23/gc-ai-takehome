## Review: eval-schema (commit 2a41d33)
## Date: 2026-04-04

---

### Standard Review

#### Edge Cases
- **types.ts:25-33 (`isEvalSuccess`)** — Guard checks `'clauses' in res` and `'overall_fairness' in res` but does not verify their types. An object like `{ error: null, overall_fairness: 42, clauses: "oops" }` passes the guard. Downstream code iterating `clauses` as an array would throw. · `[Valid]`

#### Error Handling
- **types.ts:25-33 / types.ts:35-43** — Both guards only check property existence, not value types. Since the parsed response comes from an untrusted source (Claude's output), `clauses` could be a non-array and `reason` could be a non-string. · `[Valid — overlaps with edge case above]`

#### Contract Violations
- None found.

---

### Edge Case Hunter

- **types.ts:25-33 (isEvalSuccess)** — `clauses` present but not an array → array iteration over non-array causes runtime crash · fix: `Array.isArray((res as {clauses:unknown}).clauses)` · `[Valid]`
- **types.ts:25-33 (isEvalSuccess)** — `overall_fairness` present but wrong type → downstream receives wrong type · fix: `typeof ... === 'string'` · `[Speculative — fairness is used for display, not arithmetic; low risk but cheap to guard]`
- **types.ts:25-33 (isEvalSuccess)** — empty `clauses` array with unvalidated clause shapes → malformed clause objects cause rendering errors · `[Dismissed — deep validation of each clause is overkill for MVP; the type guard's job is top-level discrimination]`
- **types.ts:35-43 (isEvalError)** — `error` field is string `'true'` instead of boolean `true` → guard returns false, error unhandled · `[Dismissed — strict `=== true` is correct; coercing stringy booleans would be a bug]`
- **types.ts:35-43 (isEvalError)** — `reason` present but not a string → display corruption · `[Speculative — cheap to guard but low risk]`
- **types.ts (both guards)** — response has `error: false` (neither null nor true) → silently unmatched · `[Speculative — this is a gap in the discriminant, but the API route controls the response shape]`
- **validation.ts** — mixed-case extension e.g. `.TXT` or `.Txt` → file rejected · `[Dismissed — `getFileExtension` already calls `.toLowerCase()` on line 7]`
- **validation.ts** — filename has no extension → unclear error message · `[Dismissed — already handled, `getFileExtension` returns `''` and `validateFileExtension` rejects it]`
- **validation.ts** — filename ends with dot (e.g. `'contract.'`) → misleading error · `[Dismissed — returns `'.'` which is not in ALLOWED_EXTENSIONS; correctly rejected]`

---

### Adversarial

1. **types.ts:6** — `clause_type` typed as open `string`, no closed set · `[Dismissed — spec defines this as free text from the model, not an enum]`
2. **types.ts:8** — `market_standard` is open `string` · `[Dismissed — free text by design]`
3. **types.ts:25-33** — `isEvalSuccess` does not validate `clauses` is an array · `[Valid — same as edge case hunter]`
4. **types.ts:25-33** — `isEvalSuccess` does not validate `call_to_action` is an array · `[Valid — `.map()` on non-array would throw]`
5. **types.ts:25-33** — `overall_fairness` only checked for presence, not valid enum value · `[Speculative — low impact for MVP display]`
6. **types.ts:35-43** — `isEvalError` too permissive, could match unrelated error objects · `[Dismissed — the only caller is the API route which controls the response shape]`
7. **types.ts (missing)** — No `EvalClause` validator · `[Dismissed — deep clause validation is M2 scope]`
8. **types.ts:4** — `section_number` doesn't enforce `§` prefix from spec examples · `[Dismissed — spec examples show `§` but don't mandate it as a format constraint]`
9. **types.ts (missing)** — `summary` allows empty string · `[Dismissed — prompt engineering handles this; type guard is for shape discrimination]`
10. **types.ts (missing)** — `call_to_action: []` on egregious contract is suspect · `[Dismissed — valid edge case for prompt, not type system]`
11. **validation.ts** — Removing `.pdf` silently breaks cached clients · `[Dismissed — no clients exist yet; this is greenfield]`
12. **validation.ts** — Case-sensitive extension check · `[Dismissed — `.toLowerCase()` already applied]`
13. **types.ts:14-17** — No shape for infrastructure failures (timeout, parse error) · `[Dismissed — API route returns 500 for these; client handles non-200 as error in later steps]`
14. **types.ts:25-33** — Cast to `EvalSuccess` before guard is proven · `[Valid — already fixed in simplify pass, now uses `{ error: unknown }`]`
15. **tests** — No rejection tests for `.pdf`/`.doc`/`.docx` · `[Dismissed — validation.test.ts already has rejection tests at lines 12-22]`

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 2 | 0 | 2 | Useful — caught the core guard weakness |
| Edge Case Hunter | 9 | 0 | 2 valid, 4 dismissed | Useful — thorough enumeration, some false positives on validation.ts |
| Adversarial | 15 | 1 (call_to_action array check) | 3 valid | Useful — found call_to_action gap others missed; high noise on dismissed items |

**Notes:** All three converged on the same core issue: type guards check property existence but not value types. Adversarial uniquely caught the `call_to_action` array check. ~60% of adversarial findings were false positives due to not reading the actual validation.ts implementation (case sensitivity, rejection tests).
