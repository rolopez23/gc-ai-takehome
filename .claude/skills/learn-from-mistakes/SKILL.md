---
name: learn-from-mistakes
description: >
  Runs before and after human sign-off on a step. Logs human corrections, missed cases, and
  implementation holes for pattern tracking. Does not fix anything — the goal is to accumulate
  insight over time. When the same class of mistake occurs 3 or more times, surfaces a concrete
  suggestion to update AGENTS.md or an existing skill.
  Trigger after automated steps complete (pre-human) and again after human sign-off (post-human).
  Also trigger when the user says "log what went wrong", "retrospective", "what did we miss",
  or "learn from this".
---

# Learn From Mistakes

You are running a lightweight retrospective on a completed step. You are not fixing anything.
You are logging what happened so that patterns can emerge over time and improve future work.

## When This Runs

This skill runs twice per step:

- **Pre-human** (after Review, before sign-off): mine the automated step outputs for gaps —
  what verify/simplify/review caught, what they missed, what required rework.
- **Post-human** (after sign-off): capture everything the human corrected or flagged that the
  automated steps did not.

The post-human run is the most important. Do not skip it or treat it as optional.

## Step 1: Read the Automated Step Outputs

Read all output files for this step:

1. `docs/<feature>/verify/<step>-*.md` — failures, incomplete checks, issues discovered
2. `docs/<feature>/simplify/<step>-*.md` — what was applied, what was suggested, any regressions
3. `docs/<feature>/reviews/<step>-*.md` — bugs, edge cases, contract violations found (or clean bill)
4. The step plan (`docs/<feature>/steps/<step-name>.md`) — compare planned vs. actual

For each file, ask: **did this step catch everything it should have?** A clean bill of health
from review is not a free pass — if a real issue emerged later, the clean bill was wrong and
that is a loggable skill gap.

## Step 2: Mine the Conversation for Human Corrections

Scroll back through the conversation for this step and extract every correction the human made.
Do not rely on the human to remember — do the work yourself. Look for:

- Messages where the human said something was wrong, missing, or not done correctly
- Places where the human asked "why wasn't X done?" or "you should have..."
- Steps the human had to request that should have happened automatically
- Anything the human had to fix themselves after the automated steps passed
- Workflow violations — steps run out of order, skipped, or executed incorrectly

For each correction found, ask:
1. Which automated step should have caught this?
2. Why didn't it?
3. Is this a one-off or a pattern?

## Step 2b: Self-Reflection (Agent Mistakes)

Before asking the human, review your own conversation history and log what YOU could have
done better. Look for:

- **Wasted turns** — retries, thrashing, wrong assumptions that burned tokens and time
- **Questions you shouldn't have asked** — things you should have just done (e.g., "should I verify?")
- **Missing context you should have requested upfront** — what could the human have told you
  at the start that would have gotten you to the right answer faster and with fewer tokens?
- **Wrong order of operations** — did you do things in a suboptimal sequence?

For each, log it the same way as human corrections. The human makes mistakes too — but the
agent should be getting smarter over time. Both sides learning is the goal.

## Step 3: Ask the Human Directly

After mining the conversation, ask the human these specific questions — do not bundle them
into one vague question:

1. "Were there any corrections you made that I haven't mentioned above?"
2. "Did any automated step give you false confidence — passed when something was actually wrong?"
3. "Was anything in the workflow unclear or out of order?"
4. "Is there a rule you'd want me to follow every time that I didn't follow here?"
5. "Is there any context you could have given me upfront that would have gotten us here faster?"

Wait for responses before writing the log entries. Every answer is a candidate log entry.

## What Counts as a Loggable Event

Log an event when something required unexpected correction or was missed by an earlier step.
Categories:

- **Human correction** — the human changed or rejected something after automated steps passed
- **Missed edge case** — a case not caught by tests, verify, or review that surfaced later
- **Implementation hole** — something in the spec that wasn't implemented, discovered late
- **Bad assumption** — code was written based on an assumption that turned out to be wrong
- **Large refactor** — a significant simplification that was only caught in the simplify step
- **Skill gap** — a class of problem the review/simplify/verify skills consistently miss
- **Test gap** — automated tests passed but the behavior was still wrong

Do not log:

- Small things caught and handled cleanly in the normal course of the workflow
- Style preferences or subjective disagreements
- One-off environmental issues (server wasn't running, wrong config)

## The Learning Log

Append entries to `.claude/learnings.md`. Create the file if it doesn't exist.

Each entry follows this format:

```markdown
### <YYYY-MM-DD> · <feature>/<step>

**Category**: <Human correction | Missed edge case | Implementation hole | Bad assumption | Large refactor | Skill gap | Test gap>
**Error class**: <Specification | Skill | Context | Prompt>
**What happened**: <1–2 sentences describing the specific mistake or gap>
**Where it surfaced**: <which step caught it, or "human review">
**Pattern tag**: `<short-kebab-case-tag>` (e.g. `nil-not-checked`, `auth-missing`, `off-by-one`, `concurrent-write`)
```

### Error Classes

Every entry must be classified. This tells us where to fix:

| Class | Definition | Fix lives in |
|---|---|---|
| **Specification** | The spec was wrong, incomplete, ambiguous, or didn't match the implementation contract (e.g. field names, casing, missing edge definitions) | Update `/problem-spec` or the spec itself |
| **Skill** | A skill's instructions produced wrong output — missed a bug, applied an unsafe change, gave a clean bill incorrectly | Update the skill's SKILL.md |
| **Context** | The agent had wrong context, didn't follow the workflow, or bypassed skills with raw agents | Update AGENTS.md or workflow enforcement |
| **Prompt** | The user's request was ambiguous, misleading, or missing critical detail that led to wrong implementation | Note for future — the stress-test in `/problem-spec` should catch these |

When the same **error class + pattern tag** combination recurs, the suggested fix targets the
right layer — not just "add a rule" but "fix this specific skill" or "catch this in the spec."

The pattern tag is the key field — it's how recurring issues are detected.

## Detecting Patterns

After appending the new entries, scan `.claude/learnings.md` for pattern tags that appear
3 or more times. For each such tag:

1. List the occurrences (dates, features, brief descriptions)
2. Check the error class distribution for this tag — are they all the same class?
3. Route the fix based on the dominant error class:
   - **Specification** → update `/problem-spec` skill (add to stress-test) or suggest spec template change
   - **Skill** → update the specific skill that missed it (name the skill and what to add)
   - **Context** → add a rule to AGENTS.md or update workflow enforcement
   - **Prompt** → note it; suggest the user add it to their own CLAUDE.md conventions
4. Draft the suggestion (see format below) but do not apply it — present it to the user

## Suggesting a Fix

When a pattern crosses the 3-occurrence threshold, output:

```
## Pattern Detected: `<tag>`

Occurred <N> times:
- <date> · <feature/step> — <one-line summary>
- ...

**Suggested fix:**
→ **AGENTS.md addition**: "<the rule to add, written as a direct instruction>"
— or —
→ **Skill update** (<skill name>): "<what to add or change in the skill, and where>"

Apply this? (yes / no / later)
```

Wait for the user's response before making any changes to AGENTS.md or skill files.

## Save the Output

Append to `.claude/learnings.md` (the cumulative log). Also save or update a per-step summary
at `docs/learnings/<feature>-<step>-<YYYY-MM-DD>.md`. If the file already exists from a
pre-human run, append a `## Post-Human Additions` section rather than overwriting.

Tell the user:
- How many new events were logged
- Whether any patterns crossed the threshold
- Where the files were saved

## Update the Plan (MANDATORY)

**You MUST update plan.md immediately after this skill completes — not later, not batched.**
After the post-human run, mark the Human column ✅ in plan.md.
