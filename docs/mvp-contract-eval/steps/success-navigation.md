# Step: success-navigation

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

On successful evaluation, the app generates a UUID, stores the result in a React context, and navigates to `/contract/[uuid]`. This step also creates the `EvalResultContext` provider (wrapping the app layout) and the minimal results page at `/contract/[id]/page.tsx`.

## Done When

- A successful evaluation generates a UUID and calls `router.push('/contract/[uuid]')`
- The evaluation result is stored in `EvalResultContext` keyed by UUID
- `/contract/[id]` reads the result from context and displays "Evaluation complete" with the `overall_fairness` value
- `/contract/[id]` with no matching result shows "No evaluation found"
- All tests pass

## Cycles

### eval-result-context

**Test** — write these tests in `frontend/__tests__/success-navigation.test.tsx` and confirm they fail:
- **stores and retrieves a result by UUID**: render a test component inside the provider → call `setResult(uuid, evalSuccess)` → call `getResult(uuid)` → assert it returns the stored value
- **returns undefined for unknown UUID**: call `getResult('nonexistent')` → assert undefined

Setup: create a small test harness component that uses the context.

**Code** — Create `frontend/app/evaluate-contract/eval-result-context.tsx`:
- `EvalResultContext` with `setResult(id: string, result: EvalResponse)` and `getResult(id: string): EvalResponse | undefined`
- `EvalResultProvider` component that wraps children and manages a `Map<string, EvalResponse>` via `useRef`
- Export `useEvalResult()` hook

Update `frontend/app/layout.tsx` to wrap with `EvalResultProvider`.

**Refactor** — none

**Commit**: `Add EvalResultContext for client-side result storage`

---

### navigate-on-success

**Test** — write these tests and confirm they fail:
- **navigates to /contract/[uuid] on success**: render evaluate page → set file → click Evaluate → resolve fetch with valid `EvalSuccess` → assert `router.push` was called with a path matching `/contract/`
- **UUID is a valid format**: capture the push argument → assert it matches `/contract/` followed by a UUID-like string

Setup: mock `next/navigation`'s `useRouter`. Mock `crypto.randomUUID`.

**Code** — Update `handleSubmit` in `page.tsx`:
- After parsing a successful response: `const id = crypto.randomUUID()`
- `setResult(id, parsed)` via context
- `router.push(`/contract/${id}`)`

**Refactor** — none

**Commit**: `Navigate to /contract/[uuid] on successful evaluation`

---

### results-page

**Test** — write these tests and confirm they fail:
- **shows evaluation complete for valid result**: render `/contract/[id]` with a success result in context → assert "Evaluation complete" text is visible
- **shows overall fairness value**: assert the fairness value from the result is displayed
- **shows no evaluation found when result missing**: render `/contract/[id]` with no result in context → assert "No evaluation found" is visible

Setup: wrap test renders in `EvalResultProvider` pre-loaded with test data.

**Code** — Create `frontend/app/contract/[id]/page.tsx`:
- Read `id` from `params`
- Call `useEvalResult().getResult(id)`
- If result exists and `isEvalSuccess(result)`: render "Evaluation complete — {overall_fairness}"
- If no result: render "No evaluation found"

**Refactor** — none

**Commit**: `Add minimal results page at /contract/[id]`

---

## LLM Verification

With the dev server running:

1. Open `http://localhost:3000/evaluate-contract`
2. Upload a `.txt` training contract
3. Click "Evaluate Contract"
4. Observe: shimmer → browser navigates to `/contract/[some-uuid]`
5. Page shows "Evaluation complete — egregious" (or whichever fairness tier)
