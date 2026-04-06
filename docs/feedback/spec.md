# Spec: User Feedback on Clause and Review Evaluations

## Problem Statement

Users viewing a completed lease evaluation have no way to signal whether the AI's analysis is
helpful or accurate. Adding per-clause and per-review feedback (thumbs up/down + optional text)
closes this loop and provides a foundation for quality measurement.

## What We Are Solving

- Two new database tables: `review_feedback` (overall score) and `clause_feedback` (per-clause).
- API endpoints to upsert and read feedback for reviews and clauses.
- Frontend UI: thumbs up/down buttons + optional text input on each `ClauseCard` and on the
  overall score area of the review page.
- Upsert semantics: re-submitting feedback overwrites the previous record.
- Vote change clears any existing comment (stale comment on a flipped vote is assumed bad).
- Each thumb click and each text submission fires a debounced PUT independently.

## What We Are NOT Solving

- User authentication or identity — single-user app, feedback is implicitly the requester's.
- Feedback aggregation, analytics, or admin dashboard.
- Feedback on summary text or call-to-action items (only clauses and overall score).
- Any changes to the evaluation pipeline or AI prompts based on feedback.
- Server-side enforcement of review completion status (frontend gates visibility instead).
- Re-running reviews — clauses are immutable once a review completes.

## Actors & Triggers

- **Actor**: End user viewing a contract review (any status, but UI only shows feedback controls
  on completed reviews).
- **Trigger**: User hovers over a clause card or the overall score area, revealing feedback
  controls. User clicks thumbs-up or thumbs-down, or submits/edits comment text.

## Success Criteria

- Each `ReviewClause` can have exactly one `clause_feedback` record.
- Each `ContractReview` can have exactly one `review_feedback` record.
- Feedback persists across page reloads — the UI reflects saved state on next hover.
- User can change their vote or edit text after initial submission (upsert).
- Changing a vote clears any existing comment.
- Feedback controls only render when review status is "completed".

## Frontend Behavior

### Deferred Loading

- Feedback data is **not** fetched on initial page load — it must not delay rendering.
- Feedback is fetched lazily: on first hover over the overall score area or any clause card,
  a single bulk fetch retrieves all feedback for the review (both review-level and clause-level).
- Until the fetch completes, feedback controls are not shown (no loading skeleton in the
  hover state — just don't render controls until data arrives).
- Once fetched, feedback state is cached client-side for the duration of the page session.

### Hover-to-Reveal

- Feedback controls (thumbs up/down + optional comment input) appear when the user hovers
  over a clause card or the overall score area.
- Controls disappear when the user's cursor leaves the clause card or score area,
  **unless the comment input is focused** — in that case, controls stay visible until
  the input loses focus (prevents mid-typing disappearance).
- If feedback has already been submitted for a target, the saved vote is shown as selected
  and any comment is displayed on hover.

### Debouncing

- Thumb clicks and text submissions are debounced at **300ms** before firing the PUT.
- If the user rapidly toggles votes, only the final state is sent.
- In-flight requests are cancelled (AbortController) when a new interaction supersedes them.

## Interfaces

### Schemas

**New table: `review_feedback`**

| Column        | Type            | Constraints                          |
|---------------|-----------------|--------------------------------------|
| `id`          | UUID            | PK, default gen                      |
| `review_id`   | UUID            | FK -> contract_reviews.id, UNIQUE, NOT NULL |
| `vote`        | String          | NOT NULL, enum: "up", "down"         |
| `comment`     | Text (nullable) |                                      |
| `created_at`  | DateTime (tz)   | default now                          |
| `updated_at`  | DateTime (tz)   | default now, onupdate now            |

**New table: `clause_feedback`**

| Column        | Type            | Constraints                          |
|---------------|-----------------|--------------------------------------|
| `id`          | UUID            | PK, default gen                      |
| `clause_id`   | UUID            | FK -> review_clauses.id, UNIQUE, NOT NULL |
| `vote`        | String          | NOT NULL, enum: "up", "down"         |
| `comment`     | Text (nullable) |                                      |
| `created_at`  | DateTime (tz)   | default now                          |
| `updated_at`  | DateTime (tz)   | default now, onupdate now            |

No NULL-in-unique-key issues — each table has a simple single-column unique constraint.

**Touched tables (read-only)**: `contract_reviews`, `review_clauses` — FK references only.

### Contracts

**New endpoints:**

| Method | Path | Body | Response | Purpose |
|--------|------|------|----------|---------|
| PUT | `/api/reviews/{review_id}/feedback` | `{ vote: "up"\|"down", comment?: string }` | `ReviewFeedbackOut` | Upsert review-level feedback |
| GET | `/api/reviews/{review_id}/feedback` | — | `ReviewFeedbackOut \| null` | Get review-level feedback |
| PUT | `/api/clauses/{clause_id}/feedback` | `{ vote: "up"\|"down", comment?: string }` | `ClauseFeedbackOut` | Upsert clause-level feedback |
| GET | `/api/reviews/{review_id}/clause-feedback` | — | `list[ClauseFeedbackOut]` | Get all clause feedback for a review |

**PUT behavior**: The body always contains `vote`. If `comment` is omitted or null, the
server clears any existing comment. This ensures vote changes don't leave stale comments.

**Response schemas:**
- `ReviewFeedbackOut`: `{ id, review_id, vote, comment, created_at, updated_at }`
- `ClauseFeedbackOut`: `{ id, clause_id, vote, comment, created_at, updated_at }`

### Existing Code

| File | Role | Change |
|------|------|--------|
| `backend/models.py` | SQLAlchemy models | Add `ReviewFeedback` + `ClauseFeedback` models |
| `backend/schemas.py` | Pydantic schemas | Add `FeedbackIn`, `ReviewFeedbackOut`, `ClauseFeedbackOut` |
| `backend/routers/reviews.py` | Review endpoints | Add review feedback PUT/GET + clause feedback GET |
| `backend/routers/` | New or existing router | Add clause feedback PUT |
| `frontend/app/evaluate-contract/types.ts` | TS types | Add `ReviewFeedback`, `ClauseFeedback` types |
| `frontend/app/contract/[id]/ClauseCard.tsx` | Clause display | Add hover-reveal feedback controls |
| `frontend/app/contract/[id]/page.tsx` | Review page | Add overall-score hover feedback, lazy fetch, gate on completed status |

### Shared State

- `review_feedback` references `contract_reviews` via FK.
- `clause_feedback` references `review_clauses` via FK.
- Frontend lazily fetches all feedback on first hover, caches client-side, fires debounced
  PUTs on interaction.

## Open Questions

None — scope is locked.
