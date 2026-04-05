# Step: loading-shimmer

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

The evaluate-contract page gets a real submit flow: clicking "Evaluate Contract" reads the file text, POSTs it to `/api/evaluate`, and shows a skeleton shimmer loading state while waiting. The button is disabled during the call. This is the first step that wires the page to the API route.

## Done When

- Clicking Evaluate with a staged file sends the file text to `/api/evaluate` via `fetch`
- A skeleton shimmer (animated placeholder) appears while the call is in flight
- The Evaluate button is disabled and visually dimmed during the call
- The FileDropZone and textarea are hidden or replaced by the shimmer during loading
- When the response arrives, the shimmer disappears (success/error handling comes in later steps)
- All tests pass

## Cycles

### submit-and-loading-state

**Test** — write these tests in `frontend/__tests__/loading-shimmer.test.tsx` and confirm they fail:
- **shows shimmer when submitting**: render page → set a file via FileDropZone → click Evaluate → assert an element with `data-testid="loading-shimmer"` is visible
- **disables button when submitting**: render page → set file → click Evaluate → assert button is disabled
- **hides shimmer when response arrives**: render page → set file → click Evaluate → resolve fetch → assert shimmer is gone and button is enabled again

Setup: mock `fetch` to return a controllable promise. Use `@testing-library/react` + `userEvent`.

**Code** — Update `frontend/app/evaluate-contract/page.tsx`:
- Add `isLoading` state (boolean, initially false)
- Replace stub `handleSubmit` with async function:
  1. Set `isLoading = true`
  2. Read file text: `const text = await file.text()`
  3. `fetch('/api/evaluate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) })`
  4. Set `isLoading = false` in a `finally` block
- When `isLoading` is true: render a shimmer skeleton div (Tailwind `animate-pulse` with gray background bars) and disable the button
- When `isLoading` is false: render the normal form

**Refactor** — none

**Commit**: `Add loading shimmer and wire evaluate button to /api/evaluate`

---

## LLM Verification

**N/A** — loading state is transient UI; verified via unit tests. Real E2E verification happens after success-navigation step.
