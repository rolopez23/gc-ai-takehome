# Step: eval-schema

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

TypeScript types for the evaluation response (success and error), runtime type guard functions to safely narrow API responses, and narrowing `ALLOWED_EXTENSIONS` to `.txt` only. After this step, all downstream code has typed contracts to import.

## Done When

- `EvalSuccess`, `EvalError`, and `EvalResponse` types exist and are importable
- `isEvalSuccess()` and `isEvalError()` type guards work correctly at runtime
- `ALLOWED_EXTENSIONS` only contains `.txt`
- All existing validation tests still pass
- New type guard tests pass

## Cycles

### response-types

**Test** — write these tests and confirm they fail:
- **isEvalSuccess returns true for valid success response**: asserts `isEvalSuccess({ error: null, overall_fairness: "fair", summary: "...", call_to_action: [], clauses: [] })` is `true`
- **isEvalSuccess returns false for error response**: asserts `isEvalSuccess({ error: true, reason: "not a contract" })` is `false`
- **isEvalError returns true for error response**: asserts `isEvalError({ error: true, reason: "..." })` is `true`
- **isEvalError returns false for success response**: asserts `isEvalError({ error: null, overall_fairness: "fair", summary: "", call_to_action: [], clauses: [] })` is `false`

**Code** — Create `frontend/app/evaluate-contract/types.ts`:

```typescript
export interface EvalClause {
  section_number: string;
  clause_type: string;
  purpose: string;
  fairness: 'fair' | 'unfair' | 'egregious';
  market_standard: string;
  explanation: string;
}

export interface EvalSuccess {
  error: null;
  overall_fairness: 'fair' | 'unfair' | 'egregious';
  summary: string;
  call_to_action: string[];
  clauses: EvalClause[];
}

export interface EvalError {
  error: true;
  reason: string;
}

export type EvalResponse = EvalSuccess | EvalError;

export function isEvalSuccess(res: unknown): res is EvalSuccess {
  return (
    typeof res === 'object' &&
    res !== null &&
    'error' in res &&
    (res as EvalSuccess).error === null &&
    'overall_fairness' in res &&
    'clauses' in res
  );
}

export function isEvalError(res: unknown): res is EvalError {
  return (
    typeof res === 'object' &&
    res !== null &&
    'error' in res &&
    (res as EvalError).error === true &&
    'reason' in res
  );
}
```

**Refactor** — none

**Commit**: `Add evaluation response types and type guards`

---

### narrow-extensions

**Test** — write these tests and confirm they fail:
- **ALLOWED_EXTENSIONS contains only .txt**: asserts `ALLOWED_EXTENSIONS` deep-equals `['.txt']`
- **validateFileExtension rejects .pdf**: asserts `validateFileExtension('contract.pdf')` returns `false`
- **validateFileExtension rejects .docx**: asserts `validateFileExtension('contract.docx')` returns `false`
- **validateFileExtension accepts .txt**: asserts `validateFileExtension('contract.txt')` returns `true`

**Code** — Update `frontend/app/evaluate-contract/validation.ts`: change `ALLOWED_EXTENSIONS` to `['.txt'] as const`. Update `FileDropZone.tsx` accepted extensions display if it references the old list (it imports `ALLOWED_EXTENSIONS` so display updates automatically).

**Refactor** — remove `.pdf`, `.doc`, `.docx` from any hardcoded strings in FileDropZone if present

**Commit**: `Narrow allowed extensions to .txt only for MVP`

---

## LLM Verification

**N/A** — no external surface; pure types and validation logic tested via unit tests.
