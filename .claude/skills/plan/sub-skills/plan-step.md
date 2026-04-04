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
- If this step has an externally observable surface, fill in the LLM Verification section
  with the exact command and expected output. If not, mark N/A and say why.

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

## LLM Verification

<exact command and what a passing result looks like>

— or —

**N/A** — <reason>
```
