# Step: clause-feedback-ui

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Wires `FeedbackControls` into `ClauseCard` and threads feedback props through `ClauseSection`.
After this step, hovering over any clause card in a completed review reveals feedback controls.
Feedback persists across page reloads.

## Done When

- Hovering a clause card shows thumbs up/down buttons + comment input
- Controls disappear on mouse leave unless comment input is focused (focus-lock)
- Clicking a thumb persists (visible on re-hover and page reload)
- Vote change clears comment
- First hover triggers lazy fetch of all feedback
- Vitest tests green, Playwright verification passes

## Dependencies

- **feedback-frontend-plumbing** (types, hook, component exist)
- **clause-feedback-upsert** + **clause-feedback-bulk-read** (API endpoints exist)

## Cycles

### clause-card-hover

**Test** — write `frontend/app/contract/[id]/__tests__/ClauseCard.test.tsx` and confirm they fail:
- **test_no_feedback_controls_without_hover**: render `ClauseCard` with `feedbackLoaded={true}`.
  Assert no "Thumbs up" button present (controls hidden until hover).
- **test_feedback_controls_shown_on_hover**: render with `feedbackLoaded={true}`. Fire
  `mouseEnter`. Assert "Thumbs up" and "Thumbs down" buttons appear.
- **test_feedback_controls_hidden_on_leave**: hover, then `mouseLeave`. Assert thumbs gone.
- **test_hover_calls_on_hover_start**: render with `onHoverStart={vi.fn()}`. Fire `mouseEnter`.
  Assert `onHoverStart` called.
- **test_no_controls_when_not_loaded**: render with `feedbackLoaded={false}`. Hover. Assert
  no thumbs buttons.
- **test_existing_feedback_shown**: render with `feedback={{ vote: "down", ... }}`,
  `feedbackLoaded={true}`. Hover. Assert "Thumbs down" has `aria-pressed="true"`.
- **test_focus_lock_keeps_controls_visible**: hover card, focus comment input, fire
  `mouseLeave`. Assert controls still visible. Then blur input. Assert controls disappear.
- **test_clause_card_renders_without_feedback_props**: render `ClauseCard` with only `clause`
  and `fairness` (no feedback props). Assert renders clause content normally with no errors
  (backwards-compatible).
- **test_click_thumb_calls_on_feedback_submit**: hover, click "Thumbs up". Assert
  `onFeedbackSubmit` called with `("up")`.

**Code** — Modify `frontend/app/contract/[id]/ClauseCard.tsx`:

- Convert to `"use client"` (needs useState)
- Add props: `feedback`, `onFeedbackSubmit`, `feedbackLoaded`, `onHoverStart`
- Add hover state + focus-lock via `onFocusCapture`/`onBlurCapture`
- Render `FeedbackControls` when hovered and loaded

```tsx
"use client";

import { useState } from "react";
import type {
  FairnessRating,
  ReviewClause,
  ClauseFeedback,
  Vote,
} from "@/app/evaluate-contract/types";
import FeedbackControls from "@/app/contract/[id]/FeedbackControls";

// ... existing constants ...

export default function ClauseCard({
  clause,
  fairness,
  feedback,
  onFeedbackSubmit,
  feedbackLoaded,
  onHoverStart,
}: {
  clause: ReviewClause;
  fairness: FairnessRating;
  feedback?: ClauseFeedback | null;
  onFeedbackSubmit?: (vote: Vote, comment?: string) => void;
  feedbackLoaded?: boolean;
  onHoverStart?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const showFeedback = (hovered || inputFocused) && feedbackLoaded && onFeedbackSubmit;

  return (
    <div
      className={`${CARD} border-l-2 ${FAIRNESS_BORDER[fairness]}`}
      onMouseEnter={() => {
        setHovered(true);
        onHoverStart?.();
      }}
      onMouseLeave={() => setHovered(false)}
      onFocusCapture={() => setInputFocused(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          setInputFocused(false);
        }
      }}
    >
      <h4 className={SECTION_HEADER}>
        <span className={SECTION_NUMBER}>{clause.section_number}</span>
        <span className={CLAUSE_TYPE}>{clause.clause_type}</span>
      </h4>
      <p className={EXPLANATION}>{clause.explanation}</p>
      {showFeedback && (
        <FeedbackControls
          vote={feedback?.vote ?? null}
          comment={feedback?.comment ?? null}
          onSubmit={onFeedbackSubmit}
        />
      )}
    </div>
  );
}
```

**Refactor** — none

**Commit**: `add hover-to-reveal feedback in ClauseCard`

---

### clause-section-threading

**Test** — `npx tsc --noEmit` passes (threading props is mechanical plumbing — tested
indirectly by ClauseCard tests and Playwright verification).

**Code** — Modify `frontend/app/contract/[id]/ClauseSection.tsx`:

- Add props: `clauseFeedback`, `feedbackLoaded`, `onHoverStart`, `onFeedbackSubmit`
- Thread to each `ClauseCard`

```tsx
interface ClauseSectionProps {
  rating: FairnessRating;
  clauses: ReviewClause[];
  clauseFeedback?: Map<string, ClauseFeedback>;
  feedbackLoaded?: boolean;
  onHoverStart?: () => void;
  onFeedbackSubmit?: (clauseId: string, vote: Vote, comment?: string) => void;
}
```

In the `<ClauseCard>` render:
```tsx
<ClauseCard
  clause={clause}
  fairness={rating}
  feedback={clauseFeedback?.get(clause.id) ?? null}
  feedbackLoaded={feedbackLoaded}
  onHoverStart={onHoverStart}
  onFeedbackSubmit={(vote, comment) => onFeedbackSubmit?.(clause.id, vote, comment)}
/>
```

**Refactor** — none

**Commit**: `thread feedback props through ClauseSection to ClauseCard`

---

### page-clause-wiring

**Test** — `npx tsc --noEmit` passes (page-level wiring verified via Playwright).

**Code** — Modify `frontend/app/contract/[id]/page.tsx`:

- Import `useFeedback` in `EvaluationResults`
- Pass feedback state + callbacks to `ClauseSection`

```tsx
const { clauseFeedback, loaded, fetchAll, submitFeedback } = useFeedback(result.id);

<ClauseSection
  key={rating}
  rating={rating}
  clauses={grouped[rating]}
  clauseFeedback={clauseFeedback}
  feedbackLoaded={loaded}
  onHoverStart={fetchAll}
  onFeedbackSubmit={(clauseId, vote, comment) =>
    submitFeedback({ type: "clause", clauseId }, vote, comment)
  }
/>
```

**Refactor** — none

**Commit**: `wire clause feedback into page via useFeedback hook`

---

## Verification

### Auto Tests

```bash
cd frontend
npm test -- --reporter verbose app/contract/\\[id\\]/__tests__/ClauseCard.test.tsx
npx tsc --noEmit
```

Expected: all 9 ClauseCard tests pass + tsc exits 0.

### Playwright Verification

With backend + frontend running against a completed evaluation:

```typescript
// 1. Navigate to a completed evaluation
await page.goto(`http://localhost:3000/contract/${contractId}`);

// 2. Expand a clause section
await page.getByRole("button", { name: /Dealbreaker|Non-Standard|Standard/ }).first().click();

// 3. Hover a clause card — controls appear
const clauseCard = page.locator('[class*="border-l-2"]').first();
await clauseCard.hover();
await expect(page.getByRole("button", { name: "Thumbs up" })).toBeVisible();
await expect(page.getByRole("button", { name: "Thumbs down" })).toBeVisible();

// 4. Click thumbs down
await page.getByRole("button", { name: "Thumbs down" }).click();
await expect(page.getByRole("button", { name: "Thumbs down" })).toHaveAttribute("aria-pressed", "true");

// 5. Comment input appears — type and submit
const commentInput = page.getByPlaceholder("Add a comment...");
await expect(commentInput).toBeVisible();
await commentInput.fill("bad analysis");
await commentInput.press("Enter");

// 6. Move cursor away — controls disappear
await page.mouse.move(0, 0);
await expect(page.getByRole("button", { name: "Thumbs down" })).not.toBeVisible();

// 7. Hover back — previous feedback shown
await clauseCard.hover();
await expect(page.getByRole("button", { name: "Thumbs down" })).toHaveAttribute("aria-pressed", "true");
await expect(commentInput).toHaveValue("bad analysis");

// 8. Change vote — comment clears
await page.getByRole("button", { name: "Thumbs up" }).click();
await expect(commentInput).toHaveValue("");

// 9. Reload — feedback persists
await page.reload();
await page.getByRole("button", { name: /Dealbreaker|Non-Standard|Standard/ }).first().click();
await clauseCard.hover();
await expect(page.getByRole("button", { name: "Thumbs up" })).toHaveAttribute("aria-pressed", "true");

// 10. Focus-lock: type in comment, move mouse outside — controls stay
await commentInput.focus();
await commentInput.fill("testing focus lock");
await page.mouse.move(0, 0);  // mouse leaves card
await expect(commentInput).toBeVisible();  // still visible because focused

// 11. Blur — controls disappear
await page.getByRole("heading", { level: 1 }).click();  // click elsewhere to blur
await expect(page.getByRole("button", { name: "Thumbs up" })).not.toBeVisible();
```

All 11 Playwright assertions must pass.
