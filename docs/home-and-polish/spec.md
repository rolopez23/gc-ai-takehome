# Spec: Home Page Dashboard & Frontend Polish

## Problem Statement
The app currently has a dead-end home page, a status bug where evaluations appear stuck at "pending", and rough loading/error UX. Users can't see previous evaluations or navigate between them.

## What We Are Solving

- **Status bug fix** — `evaluation.py:99` flushes but never commits the "evaluating" status. Polling from a separate session only sees "pending" until the final commit. Change `flush()` to `commit()`.
- **Structured failure codes** — Add `failure_code` column to `ContractReview` with enum values: `too_large`, `timeout`, `anthropic_error`, `parse_error`, `unknown`. Set deterministically at each failure site. Frontend maps codes to user-friendly messages.
- **Home page contract dashboard** — Replace the static hero with a list of all evaluated contracts showing: name, review status, overall fairness rating. Each row links to `/contract/[uuid]`. Shows the **latest review** per contract (by `created_at`). Empty state shows a prominent CTA: "Evaluate your first contract" (replaces the standard evaluate button).
- **Backend list endpoint enhancement** — Extend `GET /api/contracts/` to join the latest review's status, overall_fairness, and failure_code per contract. No N+1 queries.
- **Design audit & layout improvements** — Use `/frontend-design` to produce concrete designs for: home page (dashboard + empty state), evaluate-contract page, contract detail page, loading shimmer. Measurable target: consistent spacing scale, max 3 type sizes, clear visual hierarchy.
- **Loading shimmer polish** — Staggered animation-delay on clause card placeholders. Fade/slide transition between form and shimmer states.
- **Error UX** — Show user-facing error messages on evaluation failure instead of silent form reset. Map `failure_code` to friendly messages:
  - `too_large` → "This contract is too large to evaluate. Try a shorter document."
  - `timeout` → "The evaluation timed out. Please try again."
  - `anthropic_error` → "We couldn't reach our AI service. Please try again later."
  - `parse_error` → "The AI returned an unexpected response. Please try again."
  - `unknown` → "Something went wrong. Please try again."

## What We Are NOT Solving

- Summary/clause count contradiction (deferred to agentic PR)
- Instructions passthrough (already works)
- Blob storage abstraction (S3/GCS)
- Background task durability (Celery/ARQ migration)
- Accessibility/ARIA audit (separate effort)
- Pagination or filtering on the contract list (follow-up if list grows)
- Stale "evaluating" status recovery sweep (accept risk for take-home scope)

## Actors & Triggers

- **User** visits home page → sees contract list (or empty-state CTA), clicks to detail page or starts first evaluation
- **User** uploads contract → sees loading shimmer with accurate status → sees results or friendly error
- **Background task** updates review status + failure_code → polling reflects real-time progress

## Success Criteria

1. `GET /api/contracts/` returns latest review's status, overall_fairness, and failure_code per contract
2. Home page renders contract list; each row navigable to `/contract/[uuid]`; empty state shows prominent evaluate CTA
3. Polling shows "evaluating" status during LLM processing (not stuck on "pending")
4. Loading shimmer has staggered card animations and smooth form→shimmer transition
5. Failed evaluations show a descriptive, user-facing error message derived from `failure_code`
6. All three pages (home, evaluate, detail) use consistent spacing scale, max 3 type sizes, clear visual hierarchy

## Interfaces

### Schemas

**Backend — New `failure_code` column on `ContractReview`:**
```
failure_code: str | None  # enum: too_large, timeout, anthropic_error, parse_error, unknown
```

**Backend — New `ContractListOut` schema:**
```
id: UUID
name: str
upload_type: str
created_at: datetime
review_status: str | None           # latest review's status
overall_fairness: str | None        # latest review's overall_fairness
failure_code: str | None            # latest review's failure_code
```

**Backend — Updated `ReviewOut` / `ReviewDetailOut`:**
```
# Add field:
failure_code: str | None
```

**Frontend — New Zod schema for contract list item:**
```
id: z.string().uuid()
name: z.string()
upload_type: z.string()
created_at: z.string()
review_status: z.string().nullable()
overall_fairness: FairnessRatingSchema.nullable()
failure_code: z.string().nullable()
```

**Frontend — Failure code → message mapping:**
```
FAILURE_MESSAGES: Record<string, string> = {
  too_large: "This contract is too large to evaluate. Try a shorter document.",
  timeout: "The evaluation timed out. Please try again.",
  anthropic_error: "We couldn't reach our AI service. Please try again later.",
  parse_error: "The AI returned an unexpected response. Please try again.",
  unknown: "Something went wrong. Please try again.",
}
```

### Contracts

| Endpoint | Change |
|----------|--------|
| `GET /api/contracts/` | Join latest review data, return `ContractListOut[]` |
| `GET /api/reviews/{id}` | Include `failure_code` in response |
| `GET /api/contracts/{id}/review` | Include `failure_code` in response |
| `evaluation.py:99` | `flush()` → `commit()` to fix status visibility |
| `evaluation.py` (all `_fail_review` calls) | Pass `failure_code` alongside `failure_message` |

### Existing Code

| File | Role | Changes |
|------|------|---------|
| `backend/models.py` | ORM model | Add `failure_code` column to `ContractReview` |
| `backend/schemas.py` | Pydantic schemas | Add `failure_code` to `ReviewOut`; add `ContractListOut` |
| `backend/services/evaluation.py:99` | Status update | `flush()` → `commit()` |
| `backend/services/evaluation.py` | Failure handling | Set `failure_code` at each `_fail_review` call site |
| `backend/routers/contracts.py:60-63` | List endpoint | Join latest review, new response model |
| `backend/migrations/` | DB migration | Add `failure_code` column |
| `frontend/app/page.tsx` | Home page | Replace hero with contract dashboard + empty state |
| `frontend/app/evaluate-contract/page.tsx` | Upload page | Error display with friendly messages, transitions |
| `frontend/app/evaluate-contract/LoadingShimmer.tsx` | Shimmer | Stagger animation, transitions |
| `frontend/app/evaluate-contract/types.ts` | Zod schemas | Add contract list schema, failure_code field |
| `frontend/app/contract/[id]/page.tsx` | Detail page | Design polish, show friendly error for failed reviews |

## Open Questions

None — all decisions resolved during spec interview.
