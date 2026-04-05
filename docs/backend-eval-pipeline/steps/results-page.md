# Step 13: results-page

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B3 (parallel with step 12)

## What This Step Delivers

Results page rewritten to fetch from backend by contract_id. Handles all three completion
states: success (shows clauses), not-a-contract (shows rejection message), failed (shows error).
Results survive page refresh. eval-result-context removed entirely.

## Done When

- `/contract/{contract_id}` fetches `GET /api/contracts/{contract_id}/review` on mount
- Success: displays clauses grouped by fairness, score badge, summary, call-to-action
- Not-a-contract: displays summary as rejection message (no clauses)
- Failed: displays `failure_message` as error
- Loading: shows shimmer while fetching
- 404: shows "not found" message
- Page refresh reloads from backend (no data loss)
- `eval-result-context.tsx` deleted
- `EvalResultProvider` removed from `layout.tsx`

## Cycles

### fetch-review-on-mount

**Test** — write these tests and confirm they fail:
- **test_fetches_review_by_contract_id**: Render `/contract/{id}`. Assert fetch called with `GET /api/contracts/{id}/review`. · setup: mock fetch
- **test_shows_loading_while_fetching**: Render page. Assert loading state visible before fetch resolves.
- **test_shows_not_found_on_404**: Mock fetch to return 404. Assert "not found" message.

**Code** — Rewrite `frontend/app/contract/[id]/page.tsx`:
```typescript
'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import type { ReviewResponse } from '../../evaluate-contract/types';
// ... existing display imports

export default function ContractPage() {
  const { id } = useParams<{ id: string }>();
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/contracts/${id}/review`)
      .then(res => {
        if (res.status === 404) { setNotFound(true); return null; }
        return res.json();
      })
      .then(data => { if (data) setReview(ReviewResponseSchema.parse(data)); })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);
  // ... render based on state
}
```

**Refactor** — none

**Commit**: `Fetch review from backend on results page mount`

---

### render-success-state

**Test** — write these tests and confirm they fail:
- **test_completed_shows_clauses**: Mock fetch → completed review with 3 clauses. Assert clauses rendered, grouped by fairness.
- **test_completed_shows_score_badge**: Assert ScoreBadge rendered with correct rating.
- **test_completed_shows_summary**: Assert summary text displayed.
- **test_completed_shows_call_to_action**: Assert call-to-action items displayed.

**Code** — Map `ReviewCompleted` to existing display components. The field mapping:
- `overall_fairness` → `ScoreBadge` rating (same values: fair/non-standard/dealbreaker)
- `clauses` → `ClauseSection` grouped by `fairness` (same grouping logic, clauses now have `id`)
- `summary` → summary paragraph
- `call_to_action` → bullet list

Adapt `EvaluationResults` component to accept `ReviewCompleted` type instead of old `EvalSuccess`.

**Refactor** — Update `ClauseCard` if needed for the new `ReviewClause` type (added `id` field is harmless).

**Commit**: `Render completed evaluation results from backend data`

---

### render-rejection-and-error-states

**Test** — write these tests and confirm they fail:
- **test_not_a_contract_shows_message**: Mock fetch → completed with `overall_fairness: null`, `summary: "Not a contract"`. Assert rejection message displayed, no clauses section.
- **test_failed_shows_error**: Mock fetch → failed with `failure_message: "API timeout"`. Assert error message displayed.
- **test_pending_shows_loading**: Mock fetch → pending status. Assert loading/polling state shown.

**Code** — Add branching in the render:
- `completed && overall_fairness !== null` → `EvaluationResults`
- `completed && overall_fairness === null` → rejection message using `summary`
- `failed` → error display using `failure_message`
- `pending/reading/evaluating` → loading state (poll if arriving directly, or just show status)

**Refactor** — none

**Commit**: `Handle rejection and error states on results page`

---

### remove-eval-result-context

**Test** — Verify all tests pass after removal.

**Code** — Delete:
- `frontend/app/evaluate-contract/eval-result-context.tsx`
- Remove `EvalResultProvider` from `frontend/app/layout.tsx`
- Remove any remaining imports of `useEvalResult`
- Delete or update `frontend/__tests__/` tests that reference the context

**Refactor** — Clean up imports across all modified files.

**Commit**: `Remove eval-result-context, all data fetched from backend`

---

## Verification

```
1. Start backend: cd backend && make dev
2. Start frontend: cd frontend && npm run dev

=== Test 1: Success state ===
3. Upload a contract via /evaluate-contract (step 12 must work)
4. Wait for redirect to /contract/{id}
5. Assert: results displayed with clauses, score badge, summary
6. REFRESH the page (Cmd+R)
7. Assert: results STILL displayed (fetched from backend, not lost)

=== Test 2: Not-a-contract ===
8. Upload a non-contract file (e.g., recipe.txt)
9. Wait for redirect
10. Assert: "not a contract" message displayed using summary text
11. Assert: no clause sections rendered

=== Test 3: Not found ===
12. Navigate to /contract/00000000-0000-0000-0000-000000000000
13. Assert: "not found" message displayed

=== Test 4: Build verification ===
npm run build   # zero type errors
npm test        # all tests pass
```
