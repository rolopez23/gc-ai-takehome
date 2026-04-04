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

  For each step:
    write tests (red) → write code (green) → refactor → commit
    /verify    →  E2E check against live system
    /simplify  →  clean up staged code
    /review    →  correctness and edge case check
    /pr-interactive-walkthrough  →  cognitive understanding check
    human      →  sign off

/learn-from-mistakes  →  log corrections; updates .claude/learnings.md
```

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

Rules added by `/learn-from-mistakes` when a pattern recurs 3+ times.

<!-- learned-rules -->
<!-- learned-rules-end -->
