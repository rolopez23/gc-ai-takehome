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
- Each thumb click and each text submission fires a PUT immediately (no combined submit button).
- On vote change, the frontend pulses/highlights any existing comment to draw attention to it.

## What We Are NOT Solving

- User authentication or identity — single-user app, feedback is implicitly the requester's.
- Feedback aggregation, analytics, or admin dashboard.
- Feedback on summary text or call-to-action items (only clauses and overall score).
- Any changes to the evaluation pipeline or AI prompts based on feedback.
- Server-side enforcement of review completion status (frontend gates visibility instead).

## Actors & Triggers

- **Actor**: End user viewing a contract review (any status, but UI only shows feedback controls
  on completed reviews).
- **Trigger**: User clicks thumbs-up or thumbs-down, or submits/edits comment text. Each action
  fires a PUT independently.

## Success Criteria

- Each `ReviewClause` can have exactly one `clause_feedback` record.
- Each `ContractReview` can have exactly one `review_feedback` record.
- Feedback persists across page reloads — the UI reflects saved state.
- User can change their vote or edit text after initial submission (upsert).
- Changing a vote pulses/highlights the comment field if a comment already exists.
- Comment is preserved when only the vote changes; comment is replaced when text is submitted.
- Feedback controls only render when review status is "completed".

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
| `frontend/app/contract/[id]/ClauseCard.tsx` | Clause display | Add thumbs up/down + text input |
| `frontend/app/contract/[id]/page.tsx` | Review page | Add overall-score feedback UI, fetch feedback, gate on completed status |

### Shared State

- `review_feedback` references `contract_reviews` via FK.
- `clause_feedback` references `review_clauses` via FK.
- Frontend fetches all feedback in bulk on page load, then fires individual PUTs on interaction.

## Open Questions

None — scope is locked.
