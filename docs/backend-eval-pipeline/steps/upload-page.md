# Step 12: upload-page

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B3 (parallel with step 13)

## What This Step Delivers

Upload page rewritten to POST multipart to backend, poll for review status, show progress,
and redirect to results page on completion. Removes dependency on eval-result-context.

## Done When

- File + instructions sent as multipart FormData to `POST /api/contracts/upload`
- After upload, polls `GET /api/reviews/{review_id}` every 2s
- Loading state shows status text (e.g. "Reading document...", "Evaluating contract...")
- On completed: redirects to `/contract/{contract_id}`
- On failed: shows error message from `failure_message`
- On poll timeout (10 min): shows timeout error
- Abort controller cancels on unmount
- No more dependency on `useEvalResult` / `eval-result-context`

## Cycles

### multipart-upload

**Test** — write these tests and confirm they fail:
- **test_upload_sends_formdata**: Render page, select file, enter instructions, click evaluate. Assert `fetch` called with POST, body is FormData containing `file` and `instructions`. · setup: mock fetch
- **test_upload_error_shows_message**: Mock fetch to return 400. Assert error message displayed.
- **test_upload_413_shows_size_error**: Mock fetch to return 413. Assert "too large" message.

**Code** — Rewrite `evaluateContract` in `page.tsx`:
```typescript
async function uploadContract(file: File, instructions: string, signal: AbortSignal) {
  const form = new FormData();
  form.append('file', file);
  if (instructions.trim()) form.append('instructions', instructions);
  const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/contracts/upload`, {
    method: 'POST', body: form, signal,
  });
  if (!res.ok) throw new Error(res.status === 413 ? 'File too large' : 'Upload failed');
  return UploadResponseSchema.parse(await res.json());
}
```

**Refactor** — Extract `BACKEND_URL` constant.

**Commit**: `Upload files to backend via multipart POST`

---

### polling-logic

**Test** — write these tests and confirm they fail:
- **test_polls_until_completed**: Mock fetch sequence: upload 201 → poll "evaluating" → poll "completed". Assert poll called correct number of times, returns completed data.
- **test_poll_timeout**: Mock fetch to always return "evaluating". Set short timeout for test. Assert throws timeout error.
- **test_poll_returns_failed**: Mock fetch: upload → poll "failed". Assert returns failed response.
- **test_poll_abort**: Start polling, trigger abort. Assert fetch was aborted.

**Code** — Implement polling function:
```typescript
async function pollReview(reviewId: string, signal: AbortSignal): Promise<ReviewResponse> {
  const INTERVAL = 2000;
  const TIMEOUT = 10 * 60 * 1000;
  const start = Date.now();
  while (Date.now() - start < TIMEOUT) {
    const res = await fetch(`${BACKEND_URL}/api/reviews/${reviewId}`, { signal });
    const data = ReviewResponseSchema.parse(await res.json());
    if (data.status === 'completed' || data.status === 'failed') return data;
    await new Promise(r => setTimeout(r, INTERVAL));
  }
  throw new Error('Evaluation timed out — please try again');
}
```

**Refactor** — none

**Commit**: `Add review polling with 10-minute timeout`

---

### wire-upload-flow

**Test** — write these tests and confirm they fail:
- **test_full_flow_redirects**: Render page, select file, click evaluate. Mock upload + poll (completed). Assert `router.push` called with `/contract/{contract_id}`.
- **test_shows_status_while_polling**: Mock upload → poll returns "evaluating". Assert loading state visible.
- **test_shows_reading_status**: Mock upload → poll returns "reading". Assert "Reading document" text visible.
- **test_failed_shows_error**: Mock upload → poll returns "failed". Assert error message displayed.
- **test_abort_on_unmount**: Start upload, unmount component. Assert abort triggered.

**Code** — Rewrite `handleSubmit`:
1. Call `uploadContract` → get `{contract_id, review_id}`
2. Call `pollReview(review_id)` → get terminal response
3. If completed: `router.push(/contract/${contract_id})`
4. If failed: show error from `failure_message`

Remove `useEvalResult` import, remove `crypto.randomUUID()`, remove old `evaluateContract`.

Update shimmer/loading state to show current status text.

**Refactor** — none

**Commit**: `Wire upload page to backend with polling and status display`

---

## Verification

```
1. Start backend: cd backend && make dev
2. Start frontend: cd frontend && npm run dev
3. Open http://localhost:3000/evaluate-contract
4. Select a .txt contract file
5. Enter instructions: "Focus on liability"
6. Click "Evaluate Contract"
7. Observe: loading shimmer appears
8. Observe: status text updates (Evaluating contract...)
9. Observe: redirected to /contract/{id}
10. Try uploading a .png file → error message shown
11. Try uploading without a file → button is disabled
```
