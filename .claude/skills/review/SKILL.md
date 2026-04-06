---
name: review
description: >
  Reviews staged changes or a branch diff for bugs, missed edge cases, and unhandled error
  conditions. Runs three parallel reviewers — standard correctness, exhaustive path tracing,
  and adversarial — then merges findings and reports reviewer validity.
  Trigger when the user says "review this", "check for bugs", "what did I miss", "look for
  edge cases", or when the plan dashboard's Review column needs to be updated.
---

# Review

Three independent reviewers run in parallel against the same diff. Each brings a different
lens. Findings may overlap, contradict, or be unique — that's the point. All findings are
surfaced; each is triaged before acting on it.

The three sub-skills are in `sub-skills/`:
- `standard.md` — correctness: bugs, edge cases, error handling, contract violations
- `edge-case-hunter.md` — exhaustive path tracing: every unhandled branch/boundary, JSON output
- `adversarial.md` — cynical: at least 10 issues, including speculative ones

## Step 1: Gather Context

```bash
git diff --cached          # staged changes
# or for a branch:
git diff main...HEAD
```

Also read:
- Every file touched in the diff (bugs are often visible only in context)
- `docs/<feature>/spec.md` if it exists — Success Criteria and Interfaces sections

## Step 2: Dispatch All Three in Parallel

Spawn three subagents in the same turn. Give each:
1. The full diff text
2. The spec content (if found)
3. Their sub-skill instructions from `sub-skills/<reviewer>.md`

Do not wait for one to finish before starting the others.

**Subagent prompt template:**

```
You are running a code review. Follow the instructions in the sub-skill exactly.

## Sub-skill instructions
<contents of sub-skills/<reviewer>.md>

## Diff
<git diff output>

## Spec (if available)
<spec content, or "No spec found">
```

## Step 3: Merge Findings

Once all three complete, compile the report. Include every finding — do not pre-filter.
The triage step is for the human, not for the reviewer.

For edge-case-hunter's JSON output, convert each entry to a finding line:
```
- **<location>** — <trigger_condition> → <potential_consequence> · fix: `<guard_snippet>`
```

## Step 4: Triage

For each finding, assign one of:
- **Valid** — real issue, should be fixed
- **Speculative** — plausible but unconfirmed; worth noting
- **Dismissed** — false positive or out of scope; note why

The human makes final triage calls, but pre-triage obvious false positives with a brief
reason so the human doesn't have to stop and investigate them.

## Output Format

Save to `docs/<feature>/reviews/<step-name>-<YYYY-MM-DD>.md`. Determine `<feature>` from
the plan path (e.g., `docs/eval-results-display/plan.md` → `eval-results-display`).
If no plan exists, use `docs/reviews/<branch-name>-<YYYY-MM-DD>.md` as fallback.

```markdown
## Review: <branch or "staged changes">
## Date: <date>

---

### Standard Review

#### Bugs
- **<file>:<line>** — <finding> · `[Valid | Speculative | Dismissed: <reason>]`

#### Edge Cases
- ...

#### Error Handling
- ...

#### Contract Violations
- ...

---

### Edge Case Hunter

- **<file>:<line>** — <trigger> → <consequence> · fix: `<guard>` · `[Valid | Speculative | Dismissed: <reason>]`

---

### Adversarial

1. **<file>:<line>** — <finding> · `[Valid | Speculative | Dismissed: <reason>]`
2. ...

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | N | N | N | Useful / Redundant / Noisy |
| Edge Case Hunter | N | N | N | Useful / Redundant / Noisy |
| Adversarial | N | N | N | Useful / Redundant / Noisy |

**Notes:** <anything notable about this run — e.g. "adversarial found 3 real issues standard missed",
"edge case hunter was redundant given the simplicity of this diff", etc.>
```

The **Reviewer Validity** table is the learning artifact. Over time it shows which reviewers
pull their weight on which types of changes. A reviewer that is consistently "Redundant" on
small diffs may not be worth running there; one that is consistently "Noisy" on UI changes
is worth noting.

## Update the Plan (MANDATORY)

**You MUST update plan.md immediately after this skill completes — not later, not batched.**
Update the Review column in plan.md:
- **All findings dismissed or clean** → ✅
- **Valid findings raised** → ❌ — address findings (fix or explicitly accept) before Human
  sign-off. Re-run review after fixes.
