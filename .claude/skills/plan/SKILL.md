---
name: plan
description: >
  Creates a structured implementation plan from a problem spec, breaking work into independently
  testable steps with dependency tracking and a living status dashboard.
  ONLY trigger this skill when a problem spec already exists at docs/<feature>/spec.md — if no spec
  is present, simpler ad-hoc planning suffices and this skill should not be used.
  Trigger on: "make a plan", "plan this out", "how should we implement this", "create an
  implementation plan", "break this into tasks", "what order should we build this in" — but only
  when a spec.md exists. If the user asks to plan something and there is no spec, tell them to run
  /problem-spec first.
---

# Plan Skill

You are creating a living implementation plan from a problem spec. The goal is to break the work
into steps that can be built, tested, and verified independently — and to track the state of each
step as the work proceeds.

## Before You Start

Locate the spec at `docs/<feature-name>/spec.md`. Read it fully. If it does not exist, stop:
"I need a problem spec before I can make a plan. Run /problem-spec first."

**Scope check:** If the spec covers multiple independent subsystems, suggest splitting into separate
plans before continuing — one plan per subsystem, each producing working, testable software on its
own. A plan that covers too much is worse than no plan.

## Step 1: Map the File Structure

Before decomposing into steps, map out which files will be created or modified and what each is
responsible for. This is where decomposition decisions get locked in — do it before writing tasks,
not during.

- Each file should have one clear responsibility
- Files that change together should live together; split by behavior, not by layer
- In existing codebases, follow established patterns unless a file has grown unwieldy enough that
  a split belongs in the plan

List the files explicitly:

```
Create:  src/models/notification.ts     — Notification data model
Create:  src/jobs/digest-sender.ts      — Background job: sends digest emails
Modify:  src/api/feed.ts (lines ~40–80) — Add notification feed endpoint
Test:    tests/models/notification.ts
Test:    tests/jobs/digest-sender.ts
```

This structure informs step decomposition. Each step should produce self-contained file changes
that make sense independently.

## Step 2: Decompose the Spec into Steps

Read the "What We Are Solving" and "Interfaces" sections. Using the file map from Step 1, identify
natural units of independently testable work.

A step is a unit of work that can be tested on its own. Good steps:

- Have a clear, observable outcome (something you can assert about)
- Map to a coherent layer or behavior (data model, API endpoint, background job, UI component)
- Are small enough that one person can hold the whole thing in their head
- Are large enough that testing them tells you something meaningful

Typical layers: data model → core logic → API/transport → integrations → UI. Name each step
after the E2E capability it delivers — what the user or system can do when it's done, not what
the code does internally. Use kebab-case:

```
schema → event-triggers → feed-api → email-delivery
```

Not `01-schema`, not `create-notification-table`. What does the feature do when this step is complete?

## Step 3: Map Dependencies

For each step, identify what it blocks and what blocks it. Be explicit: "step 3 cannot be
meaningfully tested until step 1 is complete" is a blocking dependency. "step 4 can be built
in parallel with step 3" is worth calling out.

Express as: step N blocks steps [X, Y]. An empty blocks list means the step is a leaf.

## Step 4: Choose a Branching Strategy

Based on step count, dependencies, and team size:

- **Single feature branch** — tightly coupled sequential steps; one branch, commits per step
- **Per-step branches** — few dependencies; steps can be reviewed and merged independently
- **Worktrees** — truly independent steps; work on them simultaneously without context-switching

State your recommendation and reasoning briefly. Record whatever the user chooses.

## Step 5: Write the Plan Document

Write to `docs/<feature-name>/plan.md`:

```markdown
# Plan: <Feature Name>

> Spec: [docs/<feature-name>/spec.md](relative-path-to-spec)

## Status Dashboard

| Step                                                      | Blocks          | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| --------------------------------------------------------- | --------------- | --------------- | :--------: | :----: | :------: | :----: | :--------: | :---: |
| [schema](steps/schema.md)                                 | event-triggers, feed-api | —      |     ⬜     |   ➖   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [event-triggers](steps/event-triggers.md)                 | feed-api        | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [feed-api](steps/feed-api.md)                             | email-delivery  | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [email-delivery](steps/email-delivery.md)                 | —               | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow order per step:** Auto Tests → Verify → Simplify → Review → Understand → Human

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: E2E check — real curl or browser automation against a live system; ➖ if no external surface
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High in the
  understanding assessment. Run with the step's commit range (before/after). Low on any file → ❌,
  follow up on low areas before sign-off
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding. Do not mark Human ✅ while any
prior column is ❌ without explicit user instruction.

---

## Branching Strategy

<one paragraph: recommended approach and why>

---

## Steps

### schema

<2–3 sentences: what this step delivers, what "done" looks like>
[→ Detailed plan](steps/schema.md)

### event-triggers

...
```

## Step 6: Write the Step Plans

For each step, write a detailed TDD implementation plan. See `sub-skills/plan-step.md`.
TDD rules (Iron Law, red-green-refactor, commit rules, red flags) live in `sub-skills/tdd.md`
— read it before implementing any cycle.

Each step plan lives at `docs/<feature-name>/steps/<step-name>.md`. The main plan links to
each one.

**No placeholders.** Every step in a sub-plan must contain what the engineer actually needs.
These are failures — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "handle edge cases" (without showing the code)
- "Write tests for the above" (without the actual test code)
- "Similar to Step N" (repeat the code — the engineer may read steps out of order)
- Steps that describe what to do without showing how

You can write all sub-plans immediately, or lazily as each step starts. If the user seems ready
to implement, write them all now. If they want to review the main plan first, write them on demand.

## Step 7: Self-Review

After writing the complete plan, check it against the spec with fresh eyes:

1. **Spec coverage** — skim each requirement in the spec. Can you point to a step that
   implements it? List any gaps and add tasks for them.
2. **Placeholder scan** — search for any of the failure patterns from Step 6. Fix them inline.
3. **Type/name consistency** — do method names, types, and property names used in later steps match
   what you defined in earlier steps? A function called `clearLayers()` in step 3 but
   `clearFullLayers()` in step 7 is a bug in the plan.

Fix issues inline — no need to re-review after fixing.

## Step 8: Readiness Gate

Before handing off to implementation, verify the plan is internally consistent. Every item
must pass — if any fails, fix it before proceeding.

- [ ] Every requirement in the spec maps to at least one step
- [ ] Every file in the file map (Step 1) is touched by at least one step
- [ ] No step references a type, method, or file not defined in the file map or an earlier step
- [ ] Dependency graph has no cycles — steps can be executed in the listed order
- [ ] Each step's "Done When" condition is observable and checkable
- [ ] No step depends on out-of-scope work from the spec

If all pass, tell the user: "Plan passes readiness gate — ready to implement." If any fail,
list failures and fix before continuing.

## Keeping the Plan Current

The plan is a living document. Update it as work progresses:

- When work on a step begins, fill in the Branch / Commit column
- When a status changes, update the emoji in the dashboard
- If tests fail or verification fails, check whether the plan missed something and update it
- If scope changes, update the step description and sub-plan

The plan is done when every dashboard cell is either ✅ or ➖.
