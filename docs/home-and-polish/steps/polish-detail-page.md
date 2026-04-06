# Step: polish-detail-page

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Polishes the contract detail page: display-tier title, blockquote-styled summary, muted text tokens, consistent spacing. Also wires `getFailureMessage` into the failed state.

## Done When

1. Title uses `text-2xl` (display tier)
2. Container uses `px-6 pt-12`
3. Summary renders as blockquote (left border accent + surface background)
4. Muted text uses `text-muted` instead of `text-foreground/60`
5. Failed state uses `getFailureMessage` for friendly error display

## Cycles

### layout-and-summary

**Test** — No automated tests (layout/CSS).

**Code** — Update `contract/[id]/page.tsx`:
- `PAGE_CONTAINER`: `px-4 py-12` → `px-6 pt-12`
- `PAGE_TITLE`: `text-3xl` → `text-2xl`
- Summary in `EvaluationResults`: replace `<p className="mt-3 text-foreground/60">` with:
  ```tsx
  <div className="mt-4 rounded-r-lg border-l-2 border-foreground/20 bg-surface py-3 pl-4 pr-4">
    <p className="text-sm text-muted">{result.summary}</p>
  </div>
  ```
- Call to action list: `text-foreground/70` → `text-muted`
- Back links: `text-foreground/60` → `text-muted`

**Refactor** — none

**Commit**: `design: polish detail page with blockquote summary and consistent typography`

---

### detail-friendly-errors

**Test** — update `contract-results-page.test.tsx`:
- **test_detail_page_shows_friendly_error**: Mock review response with `status: "failed"`, `failure_code: "anthropic_error"`. Assert "We couldn't reach our AI service" text visible.

**Code** — Update `EvaluationFailed` in `contract/[id]/page.tsx`:
- Import `getFailureMessage`
- Use `getFailureMessage(review.failure_code)` instead of raw `failure_message`
- Add `failure_code` to the type passed to `EvaluationFailed`

**Refactor** — none

**Commit**: `show friendly error on contract detail page for failed reviews`

---

## Verification

Playwright screenshots:
1. Navigate to a completed contract — confirm blockquote summary, display-tier title
2. Navigate to a failed contract — confirm friendly error message
3. Dark mode — confirm surface background on blockquote is visible, muted text readable
4. Visually evaluate: does the blockquote make the summary stand out? Is the hierarchy clearer?
