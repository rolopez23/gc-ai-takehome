# Plan Step

Produces a fine-grained implementation plan for a single step. Invoked from the plan skill
for each step in the main plan. Read `tdd.md` in this directory before implementing — the
TDD rules apply to every cycle in this plan.

## Input

- The step name and description from the main plan
- The spec (for interface and schema context)
- Any dependencies this step has on previous steps (so you know what already exists)

## Output

A markdown file at `docs/<feature-name>/steps/<step-name>.md`.

**Naming:** Use the E2E capability the step delivers — what the user or system can do when
it's done, not what the code does internally:

```
docs/notifications/steps/schema.md
docs/notifications/steps/event-triggers.md
docs/notifications/steps/feed-api.md
docs/notifications/steps/email-delivery.md
```

## Cycle Order

Each cycle is one red-green-refactor loop ending in a commit (see `tdd.md`). Order them so
each builds on what the previous committed:

1. Schema / data model — tests need something to run against
2. Core logic — pure behavior, tested in isolation
3. Integration wiring — controllers, jobs, callbacks
4. Edge cases and failure modes — after the happy path is solid

Keep each cycle to one behavior. If going green would need more than ~30 lines of new
production code, split it. Good boundaries: one validation, one service method, one
controller action, one job behavior, one integration point.

## After the Final Cycle

- Update `plan.md`: mark Auto Tests ✅ for this step
- Run LLM Verification and mark the Verify column accordingly

---

## Proof of Work

> "Your job is to deliver code you have proven to work."
> — [Simon Willison](https://simonwillison.net/2025/Dec/18/code-proven-to-work/)

Every step must include an LLM Verification section. Automated tests prove correctness to the
machine. Verification proves correctness to the human — they are complementary, not substitutes.

**Verification is evidence.** The section must contain:
1. The exact command(s) to run
2. The expected output or behavior
3. What constitutes a pass vs. fail

**Before marking ➖ (N/A), exhaust all verification paths:**

| "No external surface" | Try instead |
|---|---|
| Schema/model changes | Inspect the live DB: `\dt`, `\d tablename`, insert + query |
| Config/prompt changes | Print the output, diff against expected |
| Internal service logic | Check side effects: files written, DB rows created, logs emitted |
| Type/validation changes | Build the project, run the compiler, show zero errors |

➖ is valid only when the step has genuinely no observable effect beyond what automated tests
cover — e.g., pure refactoring of internal function signatures with no behavior change.

**Important:** Auto Tests and Verify are complementary, not interchangeable. `tsc --noEmit` or
`vitest` passing is an auto test, not verification. Verification means running the actual code
and observing its behavior: curl against a live server, Playwright against a real browser, DB
queries against real tables.

### Bad Example: Confusing Auto Tests with Verification

| Step | Auto Tests | Verify |
|------|-----------|--------|
| feedback-types | `tsc --noEmit` | 6 Vitest tests: Zod parse valid/invalid |
| feedback-hook-and-controls | `tsc --noEmit` | 8 Vitest tests for FeedbackControls |
| clause-feedback-ui | browser only | 6 Vitest tests + 14-point browser checklist |
| review-feedback-ui | `tsc --noEmit` | `tsc` + 11-point browser checklist |

**Why this is wrong:**
- `tsc --noEmit` in the Auto Tests column is not a real test — it proves the code compiles,
  not that it works. It belongs nowhere or as a secondary check.
- Vitest tests in the Verify column are auto tests, not verification. They test code in
  isolation via jsdom, not by running the real application.
- "browser only" with no automated tests means you have verification but skipped auto tests.
- The columns are swapped and muddled — auto tests should contain vitest/pytest, verification
  should contain curl/Playwright/DB inspection.

### Good Example: Verification Strategy Table

A good plan includes a summary table showing how each step is tested AND verified:

| Step | Auto Tests (vitest/pytest) | Verify (run the code) |
|------|---------------------------|----------------------|
| feedback-schema | pytest: models, constraints, schema validation | DB inspection: print columns/types |
| review-feedback-upsert | pytest: create, update, 404 | curl: PUT create, PUT update, 404 |
| review-feedback-read | pytest: exists, null, 404 | curl: GET after PUT, GET null, 404 |
| clause-feedback-upsert | pytest: create, update, 404 | curl: PUT create, PUT update, 404 |
| clause-feedback-bulk-read | pytest: list, empty, scoped, 404 | curl: GET scoped list, 404 |
| feedback-frontend-plumbing | vitest: Zod schemas + component tests | ➖ (no observable surface until wired in) |
| clause-feedback-ui | vitest: ClauseCard hover/focus-lock tests | Playwright: hover, click, comment, focus-lock, reload persistence |
| review-feedback-ui | vitest: ScoreFeedback hover/focus-lock tests | Playwright: hover, click, comment, focus-lock, reload persistence |

Note the clear separation: vitest/pytest are auto tests, curl/Playwright/DB inspection are
verification. Frontend plumbing (types, hooks, components not yet wired in) gets ➖ for verify
because there is genuinely no observable surface — but it still has auto tests.

---

## Template

```markdown
# Step: <step-name>

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

<2–3 sentences describing the E2E capability this step adds>

## Done When

<concrete, checkable condition — something you can observe or run>

## Cycles

### <behavior name>

**Test** — write these tests and confirm they fail:
- **<test name>**: <what it asserts> · setup: <any fixtures needed>

**Code** — <what to implement to make those tests pass, 1–2 sentences>

**Refactor** — <cleanup, or "none">

**Commit**: `<short commit message>`

---

### <next behavior name>

**Test** — write these tests and confirm they fail:
- **<test name>**: <what it asserts> · setup: <fixtures>

**Code** — <implementation>

**Refactor** — <cleanup, or "none">

**Commit**: `<short commit message>`

---

<repeat for each cycle>

## Verification

<exact commands to run and what a passing result looks like — this is your proof of work>

— or —

**➖ N/A** — <reason, after exhausting all verification paths listed above>
```
