# Step: review-feedback-ui

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Wires `FeedbackControls` into the overall score area (ScoreBadge) on the review page. After
this step, hovering over the score badge reveals feedback controls for the overall review.
Feedback persists across page reloads.

## Done When

- Hovering the score badge area shows thumbs up/down + comment input
- Controls disappear on mouse leave unless comment input is focused
- Submitting feedback persists (visible on re-hover and page reload)
- Vote change clears comment
- Playwright verification passes

## Dependencies

- **feedback-frontend-plumbing** (types, hook, component exist)
- **review-feedback-upsert** + **review-feedback-read** (API endpoints exist)
- **clause-feedback-ui** (page already imports `useFeedback` — we extend its usage)

## Cycles

### score-badge-feedback

**Test** — write `frontend/app/contract/[id]/__tests__/ScoreFeedback.test.tsx` and confirm
they fail. Since `EvaluationResults` is a large component with fetch/polling dependencies,
extract the score-feedback hover wrapper into a testable unit or test via a simplified render:

- **test_no_feedback_controls_without_hover**: render the score area with `loaded={true}`.
  Assert no "Thumbs up" button present.
- **test_feedback_controls_shown_on_hover**: hover the score area. Assert "Thumbs up" and
  "Thumbs down" buttons appear.
- **test_feedback_controls_hidden_on_leave**: hover, then `mouseLeave`. Assert thumbs gone.
- **test_hover_calls_fetch_all**: render with `fetchAll={vi.fn()}`. Hover. Assert `fetchAll`
  called.
- **test_no_controls_when_not_loaded**: render with `loaded={false}`. Hover. Assert no thumbs.
- **test_existing_review_feedback_shown**: render with `reviewFeedback={{ vote: "up", ... }}`,
  `loaded={true}`. Hover. Assert "Thumbs up" has `aria-pressed="true"`.
- **test_focus_lock_on_score_comment**: hover, focus comment input, `mouseLeave`. Assert
  controls still visible. Blur. Assert gone.
- **test_submit_calls_handler**: hover, click "Thumbs down". Assert submit handler called
  with correct args.

To make this testable, extract a `ScoreFeedbackArea` wrapper component from `page.tsx` that
accepts `rating`, `reviewFeedback`, `loaded`, `fetchAll`, and `onSubmit` as props. This also
keeps `page.tsx` cleaner.

**Code** — Create `frontend/app/contract/[id]/ScoreFeedbackArea.tsx` and modify `page.tsx`:

Extract score-feedback hover logic into `ScoreFeedbackArea` for testability:

**`ScoreFeedbackArea.tsx`:**
```tsx
"use client";

import { useState } from "react";
import type { FairnessRating, Vote, ReviewFeedback } from "@/app/evaluate-contract/types";
import ScoreBadge from "@/app/contract/[id]/ScoreBadge";
import FeedbackControls from "@/app/contract/[id]/FeedbackControls";

interface ScoreFeedbackAreaProps {
  rating: FairnessRating;
  reviewFeedback: ReviewFeedback | null;
  loaded: boolean;
  onHoverStart: () => void;
  onSubmit: (vote: Vote, comment?: string) => void;
}

export default function ScoreFeedbackArea({
  rating,
  reviewFeedback,
  loaded,
  onHoverStart,
  onSubmit,
}: ScoreFeedbackAreaProps) {
  const [hovered, setHovered] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const showFeedback = (hovered || inputFocused) && loaded;

  return (
    <div
      className="mt-4"
      onMouseEnter={() => { setHovered(true); onHoverStart(); }}
      onMouseLeave={() => setHovered(false)}
      onFocusCapture={() => setInputFocused(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          setInputFocused(false);
        }
      }}
    >
      <ScoreBadge rating={rating} />
      {showFeedback && (
        <FeedbackControls
          vote={reviewFeedback?.vote ?? null}
          comment={reviewFeedback?.comment ?? null}
          onSubmit={onSubmit}
        />
      )}
    </div>
  );
}
```

**In `page.tsx` `EvaluationResults`** — replace the ScoreBadge wrapper:
```tsx
const { reviewFeedback, clauseFeedback, loaded, fetchAll, submitFeedback } =
  useFeedback(result.id);

{result.overall_fairness && (
  <ScoreFeedbackArea
    rating={result.overall_fairness}
    reviewFeedback={reviewFeedback}
    loaded={loaded}
    onHoverStart={fetchAll}
    onSubmit={(vote, comment) => submitFeedback({ type: "review" }, vote, comment)}
  />
)}
```

**Refactor** — none

**Commit**: `add hover-to-reveal feedback on overall score badge`

---

## Verification

### Auto Tests

```bash
cd frontend
npm test -- --reporter verbose app/contract/\\[id\\]/__tests__/ScoreFeedback.test.tsx
npx tsc --noEmit
```

Expected: all 8 ScoreFeedback tests pass + tsc exits 0.

### Playwright Verification

With backend + frontend running against a completed evaluation:

```typescript
// 1. Navigate to a completed evaluation
await page.goto(`http://localhost:3000/contract/${contractId}`);

// 2. Hover over the score badge — controls appear
const scoreBadge = page.locator("text=Standard, text=Non-Standard, text=Dealbreaker").first();
const scoreArea = scoreBadge.locator("..");  // parent div with hover handlers
await scoreArea.hover();
await expect(page.getByRole("button", { name: "Thumbs up" })).toBeVisible();
await expect(page.getByRole("button", { name: "Thumbs down" })).toBeVisible();

// 3. Click thumbs down
await page.getByRole("button", { name: "Thumbs down" }).click();
await expect(page.getByRole("button", { name: "Thumbs down" })).toHaveAttribute("aria-pressed", "true");

// 4. Type a comment and submit
const commentInput = page.getByPlaceholder("Add a comment...");
await commentInput.fill("overall score seems wrong");
await commentInput.press("Enter");

// 5. Move cursor away — controls disappear
await page.mouse.move(0, 0);
await expect(page.getByRole("button", { name: "Thumbs down" })).not.toBeVisible();

// 6. Hover back — previous feedback shown
await scoreArea.hover();
await expect(page.getByRole("button", { name: "Thumbs down" })).toHaveAttribute("aria-pressed", "true");
await expect(commentInput).toHaveValue("overall score seems wrong");

// 7. Change vote — comment clears
await page.getByRole("button", { name: "Thumbs up" }).click();
await expect(commentInput).toHaveValue("");

// 8. Reload — feedback persists
await page.reload();
await scoreArea.hover();
await expect(page.getByRole("button", { name: "Thumbs up" })).toHaveAttribute("aria-pressed", "true");

// 9. Focus-lock: focus comment, move mouse outside — controls stay
await commentInput.focus();
await commentInput.fill("testing");
await page.mouse.move(0, 0);
await expect(commentInput).toBeVisible();

// 10. Blur — controls disappear
await page.getByRole("heading", { level: 1 }).click();
await expect(page.getByRole("button", { name: "Thumbs up" })).not.toBeVisible();
```

All 10 Playwright assertions must pass. This is the final step — once verified, the full
feedback feature is complete.
