# Step: cancel-on-unmount

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

When the user navigates away from the evaluate-contract page while an API call is in flight, the request is cancelled via `AbortController`. Prevents orphaned requests and avoids state updates on an unmounted component.

## Done When

- An `AbortController` is created for each submit and its `signal` is passed to `fetch`
- On component unmount, the controller's `abort()` is called
- An aborted fetch does not trigger the error message (it's intentional, not a failure)
- All tests pass

## Cycles

### abort-on-unmount

**Test** — write these tests in `frontend/__tests__/cancel-on-unmount.test.tsx` and confirm they fail:
- **cancels in-flight request when component unmounts**: render page → set file → click Evaluate → unmount before fetch resolves → assert `AbortController.abort` was called (or the fetch signal was aborted)
- **does not show error message on abort**: render page → set file → click Evaluate → unmount → assert no error message was set (check that the error state didn't trigger)

Setup: mock `fetch` with a never-resolving promise. Spy on `AbortController`.

**Code** — Update `frontend/app/evaluate-contract/page.tsx`:
- Store `AbortController` in a `useRef`
- In `handleSubmit`: create a new `AbortController`, store in ref, pass `signal` to `fetch`
- In the catch block: check if the error is an `AbortError` — if so, return early without setting the error state
- Add a `useEffect` cleanup that calls `controllerRef.current?.abort()` on unmount

**Refactor** — none

**Commit**: `Cancel in-flight evaluation request on unmount`

---

## LLM Verification

**N/A** — abort behavior is not observable via curl or browser; verified via unit tests.
