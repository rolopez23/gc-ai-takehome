# AGENTS.md

Read by Claude at the start of every session. Links to skill files rather than
duplicating them. For full instructions, read the linked SKILL.md.

---

## Project Context

For app context on tech stack, API routes, or purpose, see [Readme.Md](Readme.Md).

---

## Nested AGENTS.md

Check for AGENTS.md in subdirectories before starting work in them.

<!-- nested-agents-index -->
<!-- nested-agents-index-end -->

---

## Workflow

For non-trivial features, follow this order:

```
/initialize     →  write or update context files in a target project
/problem-spec   →  define the problem, produce docs/<feature>/spec.md
/plan           →  break into TDD chunks, produce docs/<feature>/plan.md

  For each step (EVERY column, in order, no skipping):
    1. write tests (red) → write code (green) → refactor → commit
    2. /verify              →  E2E check against live system
    3. /simplify            →  clean up staged code
    4. /review              →  correctness and edge case check
    5. /pr-interactive-walkthrough  →  cognitive understanding check
    6. human sign-off       →  developer approves
    7. /learn-from-mistakes →  log corrections; updates .claude/learnings.md
    8. Update plan.md dashboard after EACH column completes
    ── then proceed to the next step ──
```

**CRITICAL**: Do not skip steps or reorder them. Do not start the next step until
all columns are complete and the plan dashboard is updated. /learn-from-mistakes
runs AFTER human sign-off, BEFORE the next step — it is part of the per-step loop,
not a one-time post-feature task.

---

## Skills

| Skill | Invoke | SKILL.md |
|---|---|---|
| initialize | `/initialize` | [→](../harness/skills/initialize/SKILL.md) |
| problem-spec | `/problem-spec` | [→](../harness/skills/problem-spec/SKILL.md) |
| plan | `/plan` | [→](../harness/skills/plan/SKILL.md) |
| verify | `/verify` | [→](../harness/skills/verify/SKILL.md) |
| simplify | `/simplify` | [→](../harness/skills/simplify/SKILL.md) |
| review | `/review` | [→](../harness/skills/review/SKILL.md) |
| pr-interactive-walkthrough | `/pr-interactive-walkthrough` | [→](../harness/skills/pr-interactive-walkthrough/SKILL.md) |
| learn-from-mistakes | `/learn-from-mistakes` | [→](../harness/skills/learn-from-mistakes/SKILL.md) |
| frontend-design | `/frontend-design` | [→](../harness/skills/frontend-design/SKILL.md) |
| systematic-debugging | `/systematic-debugging` | [→](../harness/skills/systematic-debugging/SKILL.md) |
| dispatching-parallel-agents | `/dispatching-parallel-agents` | [→](../harness/skills/dispatching-parallel-agents/SKILL.md) |
| skill-creator | `/skill-creator` | [→](../harness/skills/skill-creator/SKILL.md) |
| next-react-boot | `/next-react-boot` | [→](../harness/skills/next-react-boot/SKILL.md) |
| python-psql-boot | `/python-psql-boot` | [→](../harness/skills/python-psql-boot/SKILL.md) |

---

## Behavioral Rules

### Takehome mode

This is a takehome project — optimize for speed, code quality, and polish over DX best practices. Ship fast, keep it clean.

### Main branch protection

Before pushing to `main` any commit that is **not** general setup or infrastructure, you MUST:
1. Ask the user for explicit confirmation to push.
2. Elicit the exact improvement or change being made and get sign-off.

Setup/infra work (deps, config, tooling, CI, Makefile, docker-compose, env files) may be pushed without this gate.

### TypeScript type annotations

Use implicit return types for simple helpers and when the type is obvious (e.g., a function returning a boolean comparison). Use explicit types for exported utilities with complex return types, public API contracts, or when the type isn't immediately clear from the implementation.

### Frontend testing

Follow [FrontendTesting.md](FrontendTesting.md) for all frontend test code. Key rules:
- Use RTL accessibility queries (`getByRole`, `getByLabelText`, `getByText`) — **never** `document.querySelector`
- Avoid `as` type casts on RTL queries unless accessing element-specific properties
- Use `userEvent` by default, `fireEvent` only to bypass browser behavior (e.g., testing validation of disallowed file types)
- No comments that explain what the code already shows
- Maintain **75% line coverage** minimum — run `npm run test:coverage` before PRs

---

Rules added by `/learn-from-mistakes` when a pattern recurs 3+ times.

<!-- learned-rules -->
<!-- learned-rules-end -->
