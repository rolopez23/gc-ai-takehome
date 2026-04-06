# Plan: User Feedback on Clause and Review Evaluations

> Spec: [docs/feedback/spec.md](spec.md)

## Status Dashboard

| Step                                                          | Blocks                        | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| ------------------------------------------------------------- | ----------------------------- | --------------- | :--------: | :----: | :------: | :----: | :--------: | :---: |
| [feedback-schema](steps/feedback-schema.md)                   | review-feedback-upsert, clause-feedback-upsert | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| [review-feedback-upsert](steps/review-feedback-upsert.md)    | review-feedback-read          | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [review-feedback-read](steps/review-feedback-read.md)         | feedback-frontend-plumbing    | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [clause-feedback-upsert](steps/clause-feedback-upsert.md)    | clause-feedback-bulk-read     | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [clause-feedback-bulk-read](steps/clause-feedback-bulk-read.md) | feedback-frontend-plumbing  | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [feedback-frontend-plumbing](steps/feedback-frontend-plumbing.md) | clause-feedback-ui, review-feedback-ui | — | ⬜ | ➖ | ⬜ | ⬜ | ⬜ | ⬜ |
| [clause-feedback-ui](steps/clause-feedback-ui.md)             | —                             | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [review-feedback-ui](steps/review-feedback-ui.md)             | —                             | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow order per step:** Auto Tests → Verify → Simplify �� Review → Understand → Human

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: Proof the code works — real curl, Playwright browser automation, DB inspection. ➖ only when genuinely no observable effect exists.
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding.

---

## Verification Strategy

| Step | Auto Tests (vitest/pytest) | Verify (run the code) |
|------|---------------------------|----------------------|
| feedback-schema | pytest: models, constraints, schema validation | DB inspection: print columns/types |
| review-feedback-upsert | pytest: create, update clears comment, 404 | curl: PUT create, PUT update, 404 |
| review-feedback-read | pytest: exists, null, 404 | curl: GET after PUT, GET null, 404 |
| clause-feedback-upsert | pytest: create, update clears comment, 404 | curl: PUT create, PUT update, 404 |
| clause-feedback-bulk-read | pytest: list, empty, scoped, 404 | curl: GET scoped list, 404 |
| feedback-frontend-plumbing | vitest: 6 Zod + 8 FeedbackControls | ➖ (no observable surface until wired in) |
| clause-feedback-ui | vitest: 9 ClauseCard tests (hover, leave, focus-lock, backwards-compat) | Playwright: 11 assertions (hover, click, comment, focus-lock, reload persistence) |
| review-feedback-ui | vitest: 8 ScoreFeedback tests (hover, leave, focus-lock, submit) | Playwright: 10 assertions (hover, click, comment, focus-lock, reload persistence) |

---

## File Map

```
Modify:  backend/models.py                                    — Add ReviewFeedback + ClauseFeedback models
Modify:  backend/schemas.py                                   — Add FeedbackIn, ReviewFeedbackOut, ClauseFeedbackOut
Modify:  backend/routers/reviews.py                           — Add all 4 feedback endpoints
Create:  backend/tests/test_feedback.py                       — Feedback API tests
Modify:  frontend/app/evaluate-contract/types.ts              — Add feedback Zod schemas + types
Create:  frontend/app/contract/[id]/FeedbackControls.tsx      — Thumbs up/down + comment input component
Create:  frontend/app/contract/[id]/useFeedback.ts            — Hook: lazy fetch, cache, debounced upsert
Create:  frontend/app/contract/[id]/ScoreFeedbackArea.tsx     — Score badge hover + feedback wrapper (testable)
Create:  frontend/app/contract/[id]/__tests__/FeedbackControls.test.tsx — Component unit tests
Create:  frontend/app/contract/[id]/__tests__/ClauseCard.test.tsx       — ClauseCard hover tests
Create:  frontend/app/contract/[id]/__tests__/ScoreFeedback.test.tsx    — ScoreFeedbackArea hover tests
Create:  frontend/app/evaluate-contract/__tests__/feedback-types.test.ts — Zod schema tests
Modify:  frontend/app/contract/[id]/ClauseCard.tsx            — Wrap with hover-to-reveal feedback
Modify:  frontend/app/contract/[id]/ClauseSection.tsx         — Thread feedback props to ClauseCard
Modify:  frontend/app/contract/[id]/page.tsx                  — Use ScoreFeedbackArea, lazy fetch, gate on completed
```

---

## Branching Strategy

Single feature branch (`feat/agentic-eval-pipeline`). Use worktrees for parallel agent work,
merge back to the main session for quality gates.

---

## Parallelization Strategy

### Constraints

- Skills (`/verify`, `/simplify`, `/review`) cannot run in sub-agents on worktrees.
- V/S/R require the full context of a single Claude session to be valuable.
- Agents only do: TDD cycles (implement + auto tests) → mark Auto Tests column.
- Agents leave V/S/R columns ⬜ — these are handled after merge in the main session.

### Dependency Graph

```
                    feedback-schema (Phase 1 — main session)
                    /              \
   review-feedback-upsert    clause-feedback-upsert    feedback-frontend-plumbing
          |                         |                          |
   review-feedback-read      clause-feedback-bulk-read         |
          \                        /                          /
           ---- Phase 3: merge + V/S/R (main session) ------
                          |
                  clause-feedback-ui   (Phase 4 — main session)
                          |
                  review-feedback-ui   (Phase 4 — main session)
```

### Execution Phases

| Phase | Steps | Execution | V/S/R |
|-------|-------|-----------|-------|
| **1** | feedback-schema | Main session (sequential) | Full — small step, run immediately |
| **2** | review-feedback-upsert → review-feedback-read (Agent A) | 3 worktree agents in parallel | **Deferred** — agents do implement + auto tests only |
|       | clause-feedback-upsert → clause-feedback-bulk-read (Agent B) | | |
|       | feedback-frontend-plumbing (Agent C) | | |
| **3** | Merge all 3 worktrees | Main session | Full V/S/R pass on combined diff of all 5 steps |
| **4** | clause-feedback-ui → review-feedback-ui | Main session (sequential) | Full per step — these touch shared files (`page.tsx`) |

### Why This Split

- **Phase 2 agents** touch completely different files: Agent A (`routers/reviews.py` review
  endpoints + tests), Agent B (`routers/reviews.py` clause endpoints + tests), Agent C
  (all frontend plumbing files). No merge conflicts expected.
- **Phase 4 is sequential** because both UI steps modify `page.tsx` and share the `useFeedback`
  hook import — parallel worktrees would conflict.
- **V/S/R after merge** ensures the quality gates see the full picture: how the API endpoints
  interact, whether schemas are consistent, whether the frontend plumbing matches the API
  contracts.

### Post-Agent Dashboard State (after Phase 2, before Phase 3 merge)

| Step | Auto Tests | Verify | Simplify | Review |
|------|:----------:|:------:|:--------:|:------:|
| feedback-schema | ✅ | ✅ | ✅ | ✅ |
| review-feedback-upsert | ✅ | ⬜ | ⬜ | ⬜ |
| review-feedback-read | ✅ | ⬜ | ⬜ | ⬜ |
| clause-feedback-upsert | ✅ | ⬜ | ⬜ | ⬜ |
| clause-feedback-bulk-read | ✅ | ⬜ | ⬜ | ⬜ |
| feedback-frontend-plumbing | ✅ | ➖ | ⬜ | ⬜ |

---

## Steps

### feedback-schema

Add `ReviewFeedback` and `ClauseFeedback` SQLAlchemy models + Pydantic schemas. Done when
models import, tables create correctly, and schemas validate.

[→ Detailed plan](steps/feedback-schema.md)

### review-feedback-upsert

`PUT /api/reviews/{review_id}/feedback` — upsert review-level feedback. Omitted comment clears
existing. Done when curl creates, updates, clears comment, and 404s on missing review.

[→ Detailed plan](steps/review-feedback-upsert.md)

### review-feedback-read

`GET /api/reviews/{review_id}/feedback` — returns feedback or null. Done when curl returns
saved feedback, null for no feedback, and 404 on missing review.

[→ Detailed plan](steps/review-feedback-read.md)

### clause-feedback-upsert

`PUT /api/reviews/clauses/{clause_id}/feedback` — upsert clause-level feedback. Same semantics
as review upsert. Done when curl creates, updates, clears comment, and 404s on missing clause.

[→ Detailed plan](steps/clause-feedback-upsert.md)

### clause-feedback-bulk-read

`GET /api/reviews/{review_id}/clause-feedback` — returns all clause feedback for a review.
Done when curl returns scoped list, empty list, and 404 on missing review.

[→ Detailed plan](steps/clause-feedback-bulk-read.md)

### feedback-frontend-plumbing

Zod schemas + types, `useFeedback` hook, and `FeedbackControls` component. Internal plumbing
with no observable surface until wired into the page. Verify: ➖.

[→ Detailed plan](steps/feedback-frontend-plumbing.md)

### clause-feedback-ui

Wire `FeedbackControls` into `ClauseCard` and `ClauseSection` with hover-to-reveal and
focus-lock. Verified via Playwright: hover clause, submit feedback, reload, confirm persistence.

[→ Detailed plan](steps/clause-feedback-ui.md)

### review-feedback-ui

Wire `FeedbackControls` into the overall score area on the review page. Verified via
Playwright: hover score badge, submit feedback, reload, confirm persistence.

[→ Detailed plan](steps/review-feedback-ui.md)
