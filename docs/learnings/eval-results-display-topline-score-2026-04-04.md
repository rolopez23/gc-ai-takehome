# Learnings: eval-results-display / topline-score — 2026-04-04

## Pre-Human Run

**New loggable events:** 1

1. `unnecessary-type-cast` (3rd occurrence) — inherited `as EvalSuccess | undefined` cast from M1 stub silently skipped `EvalError` variant. Caught by correctness reviewer, not during initial file read.

**Pattern threshold crossed:** `unnecessary-type-cast` at 3 occurrences.

**Suggested fix (pending user approval):**
→ **Skill update (review/standard.md)**: Add to the Bugs checklist: "Check for `as` casts that narrow discriminated unions — these skip variants silently. Use runtime discriminant checks instead."
→ **Context update (AGENTS.md)**: Add rule: "Never use `as` to narrow discriminated unions. Use runtime checks (e.g., `x.error === null`) to let TypeScript narrow naturally."

**Workflow compliance:** All steps followed in correct order. Pre-existing test breakage caught and fixed.
