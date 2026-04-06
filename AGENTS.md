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

### Feature branch required

Before writing any feature code, check out a feature branch (e.g., `m2-eval-results-display`).
**Never commit feature work directly to main.** Only write code on main if the user explicitly
confirms they want it. Setup/infra work (deps, config, tooling, CI, env files) may go on main.

### Main branch protection

Before pushing to `main` any commit that is **not** general setup or infrastructure, you MUST:
1. Ask the user for explicit confirmation to push.
2. Elicit the exact improvement or change being made and get sign-off.

Setup/infra work (deps, config, tooling, CI, Makefile, docker-compose, env files) may be pushed without this gate.

### Remote control (web-agent) mode

When operating via remote control (mobile/web), skip all interactive human verification
steps and walkthroughs (steps 2–6 in the workflow). Instead, proceed autonomously and
maintain a running to-do list of skipped verification/cognitive processing steps so the
user can review them when back at their desk.

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

### Workflow: /learn-from-mistakes is mandatory after every sign-off

After every Human sign-off, ALWAYS run /learn-from-mistakes before proceeding to the next step. This is a blocking requirement, not optional. (Pattern `workflow-steps-skipped` — 3 occurrences as of 2026-04-04.)

### Workflow order is mandatory

The per-step workflow has **mandatory** and **variable** steps:

```
Auto Tests → Verify → Simplify → Review → [Understand] → [Human] → /learn-from-mistakes
  MANDATORY   MANDATORY  MANDATORY  MANDATORY   VARIABLE    VARIABLE     MANDATORY
```

**Mandatory steps** (never skip, never ask permission, never defer):
- **Auto Tests** — run tests, all must pass
- **Verify** — live verification (curl, browser, DB inspection) against a running system. Tests prove it to the machine; verification proves it to the human. Both required. ([ref](https://simonwillison.net/2025/Dec/18/code-proven-to-work/))
- **Simplify** — code reuse, quality, efficiency review + fixes
- **Review** — correctness review (bugs, edge cases, contract violations)
- **/learn-from-mistakes** — always runs after human sign-off, before next step

**Variable steps** (human decides whether to run):
- **Understand** — PR walkthrough; human may batch or skip
- **Human** — sign-off; human may batch across steps

Do not ask "should I run verify?" or "skip to walkthrough?" — mandatory steps just run. (Pattern `workflow-steps-skipped` — 5 occurrences, `verify-not-automatic` — 2 occurrences.)

### Background and worktree agents run the full workflow

Delegating implementation to a background or worktree agent does NOT exempt that agent from
running the mandatory workflow. Every agent that implements a step must also run: tests → verify
→ simplify → review — in order, per step. Do not split implementation from VSR across agents.
(Pattern `agents-skip-workflow` — 1 explicit occurrence + `workflow-steps-skipped` — 5 occurrences.)

### Update plan.md immediately after each column completes

Update the plan dashboard **immediately** after each workflow column completes — not at the end
of the feature. If using background agents, the agent must update plan.md before returning.
A stale dashboard is a lie about project state. (Pattern `plan-not-updated` — 3 occurrences.)

### Never commit with broken E2E

Every commit must leave the application in a functional E2E state. Transitory failures during
development are fine, but before committing: verify the app starts, serves requests, and the
change works. If E2E is broken at the end of a step, fix it or stop and report — do not commit
broken code. (Pattern `broken-app-committed` — user rule, 2026-04-05.)

<!-- learned-rules-end -->

---

## Eval Rules

Informal directional benchmarks until a full eval pipeline is built. See [eval log](docs/mvp-contract-eval/eval-log.md).

### Model constraints

Before using any Claude model for verification or production, document its constraints:
- `max_tokens` output limit
- Context window size
- Cost per million tokens (input/output)
- Any known behavioral differences (e.g., fence-wrapping, instruction following)

Do not run verification against a model without first confirming it can handle the expected output size.

### Fairness benchmarks (directional)

| Contract | Expected overall_fairness |
|---|---|
| contract_1_clean | `fair` |
| contract_2_egregious | `dealbreaker` |
| contract_3_nonstandard | `non-standard` |
| contract_4_minor_issues | `non-standard` |
| contract_5_mixed | `dealbreaker` |
| simple 4-clause (inline) | `fair` |
| non-contract (cookie recipe) | `error: true` |

These are directional — the LLM may reasonably disagree on edge cases. Track deviations in the eval log.
