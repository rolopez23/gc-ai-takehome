# Step: error-display

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

When the `/api/evaluate` call fails for any reason — network error, 500, or Claude's non-contract detection — the evaluate-contract page shows "Something went wrong. Try again." inline. The error clears when the user retries.

## Done When

- A fetch failure (network error) shows the error message
- A non-200 response shows the error message
- A response with `{ error: true, ... }` from Claude shows the error message
- The error message clears when the user clicks Evaluate again
- All tests pass

## Cycles

### show-error-on-failure

**Test** — write these tests in `frontend/__tests__/error-display.test.tsx` and confirm they fail:
- **shows error on network failure**: render page → set file → click Evaluate → reject fetch → assert "Something went wrong. Try again." is visible
- **shows error on non-200 response**: render page → set file → click Evaluate → resolve fetch with `{ ok: false, status: 500 }` → assert error visible
- **shows error when Claude returns eval error**: render page → set file → click Evaluate → resolve fetch with 200 and `{ error: true, reason: "not a contract" }` → assert error visible

Setup: mock `fetch`. Use `@testing-library/react` + `userEvent`.

**Code** — Update `frontend/app/evaluate-contract/page.tsx`:
- Add `error` state (string | null, initially null)
- In `handleSubmit`:
  - Clear `error` at the start of each attempt
  - After fetch: check `response.ok` — if not, set error
  - Parse response JSON: if `isEvalError(parsed)`, set error
  - In the catch block: set error
- Render error message below the button when `error` is set: `<p className="text-red-500">Something went wrong. Try again.</p>`

**Refactor** — none

**Commit**: `Show error message on evaluation failure`

---

### error-clears-on-retry

**Test** — write this test and confirm it fails:
- **clears error when user retries**: render page → trigger an error → set a new file → click Evaluate → resolve with success → assert error message is gone

**Code** — Already handled by clearing `error` at the start of `handleSubmit`. This test validates.

**Refactor** — none

**Commit**: `Test error clears on retry`

---

## LLM Verification

**N/A** — error state is transient UI; verified via unit tests.
