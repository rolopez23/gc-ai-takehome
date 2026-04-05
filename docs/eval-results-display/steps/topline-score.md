# Step: topline-score

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

The contract results page displays a topline score badge with the mapped display label
(Fair / Unfair / Egregious) in the appropriate color, the summary string below it, and a
navigation link back to `/evaluate-contract`. The "no evaluation found" fallback is preserved.

## Done When

The contract page renders the score badge, summary, and back link for all three fairness levels,
and shows the fallback for missing UUIDs. Covered by component tests.

## Dependencies

- `fairness-utils.ts` from the label-mapping step (provides `getFairnessDisplay`)

## Cycles

### score-badge-renders-label-and-color

**Test** — write in `frontend/__tests__/score-badge.test.tsx`:
- **renders Egregious with red styling for dealbreaker**: render `<ScoreBadge rating="dealbreaker" />`,
  assert text "Egregious" is present and element has red color class
- **renders Unfair with yellow styling for non-standard**: render `<ScoreBadge rating="non-standard" />`,
  assert text "Unfair" and yellow class
- **renders Fair with green styling for fair**: render `<ScoreBadge rating="fair" />`,
  assert text "Fair" and green class

**Code** — Create `frontend/app/contract/[id]/ScoreBadge.tsx`. A presentational component that
takes `{ rating: FairnessRating }`, calls `getFairnessDisplay(rating)`, and renders the label
in a styled badge element.

**Refactor** — none

**Commit**: `Add ScoreBadge component with color-coded fairness labels`

---

### page-renders-topline-and-summary

**Test** — write in `frontend/__tests__/contract-results-page.test.tsx`:

Mock `next/navigation` to return a test UUID via `useParams`. Mock `useEvalResult` to return a
test `EvalSuccess` with `overall_fairness: 'dealbreaker'` and a known summary string.

- **renders score badge with correct label**: assert "Egregious" text is visible
- **renders summary text**: assert the summary string is visible

**Code** — Modify `frontend/app/contract/[id]/page.tsx`: replace the raw `overall_fairness`
text with `<ScoreBadge rating={result.overall_fairness} />` and keep the summary paragraph.

**Refactor** — none

**Commit**: `Wire ScoreBadge and summary into contract results page`

---

### back-link-to-upload

**Test** — add to `frontend/__tests__/contract-results-page.test.tsx`:
- **renders link back to evaluate page**: assert a link with `href="/evaluate-contract"` is present
  (use `getByRole('link')`)

**Code** — Add a `<Link href="/evaluate-contract">` element to the page (Next.js `Link` component).
Position it above or below the topline section.

**Refactor** — none

**Commit**: `Add navigation link back to evaluate page`

---

### fallback-for-missing-uuid

**Test** — add to `frontend/__tests__/contract-results-page.test.tsx`:
- **renders fallback when no result found**: mock `getResult` returning `undefined`, assert
  "No evaluation found" text is visible

**Code** — Already exists in the stub. Verify the test passes with the existing fallback code.
This cycle is test-only to confirm the fallback survives the page rewrite.

**Refactor** — none

**Commit**: `Add test coverage for missing-UUID fallback`

---

## LLM Verification

Navigate to `/contract/<test-uuid>` in the browser after evaluating a contract. Verify:
- Score badge shows the correct mapped label with color
- Summary string is visible below the badge
- Back link navigates to `/evaluate-contract`
