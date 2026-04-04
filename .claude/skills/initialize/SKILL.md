---
name: initialize
description: >
  Installs this harness's skills into a project by writing or updating AGENTS.md and/or
  CLAUDE.md with a skills reference and canonical workflow. Run this when setting up a new
  project, onboarding a repo to the spec→plan→TDD→verify→simplify→review→learn workflow, or
  when a project's context files are missing or don't reference these skills. Trigger when the
  user says "initialize this project", "set up AGENTS.md", "set up CLAUDE.md", "install
  skills", "onboard this repo", or "add skills to this project".
---

# Initialize

Install this harness's skills into a target project by writing or updating its context files.

Claude Code reads **CLAUDE.md** for project context. Codex and other agents read **AGENTS.md**.
Both serve the same purpose — orient the AI in a new session. This skill writes whichever
file(s) the project needs.

The goal is minimal files that link out to canonical skill files rather than duplicating their
contents. Less is more.

## Step 1: Locate the harness

The harness root is the directory containing `skills/`. Confirm the following exist:

- `skills/problem-spec/SKILL.md`
- `skills/plan/SKILL.md`
- `skills/verify/SKILL.md`
- `skills/simplify/SKILL.md`
- `skills/review/SKILL.md`
- `skills/learn-from-mistakes/SKILL.md`

Record the absolute path to the harness root. You'll use it to compute relative links.

## Step 2: Identify the target project

Usually the current working directory. If the user provided a path, use that.

If ambiguous, ask: "Which directory should I initialize — this one (`<cwd>`), or somewhere
else?"

## Step 3: Determine which files to write

Check what exists at the target project root:

| State | Action |
|---|---|
| Neither file exists | Create both CLAUDE.md and AGENTS.md |
| Only CLAUDE.md exists | Update CLAUDE.md; create AGENTS.md |
| Only AGENTS.md exists | Update AGENTS.md; create CLAUDE.md |
| Both exist | Update both |

If the user explicitly said "only CLAUDE.md" or "only AGENTS.md", respect that and skip the
other.

---

## Content blocks

Both files use the same four sections. Tailor the heading style to the file (CLAUDE.md can
use a friendlier intro; AGENTS.md is terse).

### Nested context index

```markdown
## Nested AGENTS.md / CLAUDE.md

Check for context files in subdirectories before starting work in them.

<!-- nested-agents-index -->
<!-- nested-agents-index-end -->
```

### Workflow

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

### Skills table

Replace `<harness-path>` with the actual relative or absolute path from the target project
to the harness root. Prefer relative paths when they share a common parent.

```markdown
## Skills

| Skill | Invoke | SKILL.md |
|---|---|---|
| initialize | `/initialize` | [→](<harness-path>/skills/initialize/SKILL.md) |
| problem-spec | `/problem-spec` | [→](<harness-path>/skills/problem-spec/SKILL.md) |
| plan | `/plan` | [→](<harness-path>/skills/plan/SKILL.md) |
| verify | `/verify` | [→](<harness-path>/skills/verify/SKILL.md) |
| simplify | `/simplify` | [→](<harness-path>/skills/simplify/SKILL.md) |
| review | `/review` | [→](<harness-path>/skills/review/SKILL.md) |
| learn-from-mistakes | `/learn-from-mistakes` | [→](<harness-path>/skills/learn-from-mistakes/SKILL.md) |
```

### Behavioral rules block

```markdown
## Behavioral Rules

Rules added by `/learn-from-mistakes` when a pattern recurs 3+ times.

<!-- learned-rules -->
<!-- learned-rules-end -->
```

---

## Creating a file

Write only what's needed. Minimal example:

```markdown
# CLAUDE.md

Read by Claude at the start of every session. Links to skill files — read those for full
instructions.

---

## Nested CLAUDE.md
...

---

## Workflow
...

---

## Skills
...

---

## Behavioral Rules
...
```

Use `# AGENTS.md` / `# CLAUDE.md` as the title to match the file. The body is identical
either way.

---

## Updating a file

Read the existing file. Add only what's missing — do not remove, reorder, or rewrite
anything that already exists.

Check for each section by marker:

| Section | Marker to look for |
|---|---|
| Nested index | `nested-agents-index` |
| Workflow | `## Workflow` |
| Skills table | `## Skills` |
| Behavioral rules | `learned-rules` |

For the Skills table specifically: if the section exists, check each skill row individually
and append any missing rows. Do not duplicate rows that are already present.

Append missing sections at the end of the file, separated by `---`.

---

## After Writing

Tell the user:

- Which files were created vs. updated
- Which sections were added to each
- The paths written
- One-liner next step: "Run `/problem-spec` to start your first feature, or `/plan` if you
  already have a spec."
