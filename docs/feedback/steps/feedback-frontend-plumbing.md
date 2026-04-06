# Step: feedback-frontend-plumbing

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

All internal frontend plumbing needed before wiring into the page: Zod schemas + types,
`useFeedback` hook (lazy fetch, client cache, 300ms debounce, AbortController), and
`FeedbackControls` component (thumbs up/down + comment input). None of this is observable
in the browser yet — it becomes verifiable in the next two steps.

## Done When

- Zod schemas validate feedback payloads, reject invalid votes
- `FeedbackControls` renders thumbs, highlights selected, shows comment after vote, clears comment on vote change
- `useFeedback` hook compiles and exports `fetchAll`, `submitFeedback`, `reviewFeedback`, `clauseFeedback`, `loaded`
- All vitest tests green, `tsc --noEmit` passes

## Dependencies

- None for types/component (pure frontend)
- API endpoints must exist before the hook can be tested at integration level (deferred to next steps)

## Cycles

### zod-schemas

**Test** — write `frontend/app/evaluate-contract/__tests__/feedback-types.test.ts` and confirm
they fail:
- **test_vote_schema_valid**: `VoteSchema.parse("up")` succeeds, `VoteSchema.parse("down")` succeeds
- **test_vote_schema_invalid**: `VoteSchema.parse("maybe")` throws ZodError
- **test_review_feedback_schema_valid**: parse valid payload succeeds
- **test_review_feedback_schema_invalid_vote**: parse with `vote: "maybe"` throws
- **test_clause_feedback_schema_valid**: parse valid payload succeeds
- **test_clause_feedback_schema_comment_nullable**: `comment: null` and `comment: "text"` both succeed

**Code** — Add to `frontend/app/evaluate-contract/types.ts`:
```typescript
export const VoteSchema = z.enum(["up", "down"]);

export const ReviewFeedbackSchema = z.object({
  id: z.string().uuid(),
  review_id: z.string().uuid(),
  vote: VoteSchema,
  comment: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const ClauseFeedbackSchema = z.object({
  id: z.string().uuid(),
  clause_id: z.string().uuid(),
  vote: VoteSchema,
  comment: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type Vote = z.infer<typeof VoteSchema>;
export type ReviewFeedback = z.infer<typeof ReviewFeedbackSchema>;
export type ClauseFeedback = z.infer<typeof ClauseFeedbackSchema>;
```

**Refactor** — none

**Commit**: `add feedback Zod schemas and TypeScript types`

---

### feedback-controls-component

**Test** — write `frontend/app/contract/[id]/__tests__/FeedbackControls.test.tsx` and confirm
they fail:
- **test_renders_both_thumbs**: render with `vote={null}`. Assert "Thumbs up" and "Thumbs down" buttons present.
- **test_no_comment_input_without_vote**: render with `vote={null}`. Assert no text input.
- **test_comment_input_shown_after_vote**: render with `vote="up"`. Assert text input present.
- **test_click_thumb_calls_on_submit**: render with `vote={null}`, click "Thumbs up". Assert `onSubmit("up")`.
- **test_vote_change_clears_comment**: render with `vote="up"`, `comment="old"`. Click "Thumbs down". Assert `onSubmit("down")` and input value empty.
- **test_comment_submits_on_blur**: render with `vote="up"`, type "my feedback", blur. Assert `onSubmit("up", "my feedback")`.
- **test_comment_submits_on_enter**: same but press Enter instead of blur.
- **test_selected_thumb_highlighted**: render with `vote="down"`. Assert `aria-pressed="true"` on down, `"false"` on up.

**Code** — Create `frontend/app/contract/[id]/FeedbackControls.tsx`:
```tsx
"use client";

import { useState } from "react";
import type { Vote } from "@/app/evaluate-contract/types";

const THUMB_BASE = "p-1.5 rounded transition-colors text-sm";
const THUMB_SELECTED = "bg-foreground/10 text-foreground";
const THUMB_UNSELECTED = "text-foreground/30 hover:text-foreground/60";

interface FeedbackControlsProps {
  vote: Vote | null;
  comment: string | null;
  onSubmit: (vote: Vote, comment?: string) => void;
}

export default function FeedbackControls({
  vote,
  comment,
  onSubmit,
}: FeedbackControlsProps) {
  const [localComment, setLocalComment] = useState(comment ?? "");

  function handleVote(v: Vote) {
    if (v === vote) return;
    setLocalComment("");
    onSubmit(v);
  }

  function handleCommentSubmit() {
    if (!vote) return;
    onSubmit(vote, localComment || undefined);
  }

  return (
    <div
      className="flex items-center gap-2 mt-2"
      onMouseDown={(e) => e.stopPropagation()}
    >
      <button
        type="button"
        onClick={() => handleVote("up")}
        className={`${THUMB_BASE} ${vote === "up" ? THUMB_SELECTED : THUMB_UNSELECTED}`}
        aria-label="Thumbs up"
        aria-pressed={vote === "up"}
      >
        👍
      </button>
      <button
        type="button"
        onClick={() => handleVote("down")}
        className={`${THUMB_BASE} ${vote === "down" ? THUMB_SELECTED : THUMB_UNSELECTED}`}
        aria-label="Thumbs down"
        aria-pressed={vote === "down"}
      >
        👎
      </button>
      {vote && (
        <input
          type="text"
          value={localComment}
          onChange={(e) => setLocalComment(e.target.value)}
          onBlur={handleCommentSubmit}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleCommentSubmit();
          }}
          placeholder="Add a comment..."
          className="flex-1 rounded border border-foreground/10 bg-transparent px-2 py-1 text-xs text-foreground/70 placeholder:text-foreground/30 focus:outline-none focus:border-foreground/30"
        />
      )}
    </div>
  );
}
```

**Refactor** — none

**Commit**: `add FeedbackControls component with tests`

---

### use-feedback-hook

**Test** — `npx tsc --noEmit` passes. No unit test — the hook's debounce/abort/fetch logic
is integration behavior, verified via Playwright in the clause-feedback-ui and review-feedback-ui
steps.

**Code** — Create `frontend/app/contract/[id]/useFeedback.ts` (full implementation as per spec:
lazy fetch on `fetchAll()`, optimistic update, 300ms debounced PUT, AbortController cancellation).

**Refactor** — none

**Commit**: `add useFeedback hook with lazy fetch and debounced upsert`

---

## Verification

**➖ N/A** — No observable surface. These are internal building blocks with no browser-visible
behavior until wired into ClauseCard and the score badge area in the next two steps. The
automated tests (vitest for FeedbackControls + Zod schemas, tsc for the hook) are the only
meaningful checks at this stage.
