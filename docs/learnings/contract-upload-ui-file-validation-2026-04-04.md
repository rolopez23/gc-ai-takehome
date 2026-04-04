# Learnings: contract-upload-ui / file-validation — 2026-04-04

## Post-Human Additions

4 events logged:

1. **`workflow-steps-skipped`** (×2) — Skipped simplify/review/understand after auto tests, and skipped /learn-from-mistakes after sign-off. Both are Context errors — the workflow was defined in AGENTS.md but not followed.

2. **`plan-not-updated`** — Plan dashboard left at ⬜ after completing Step 1. Context error — should update the dashboard as each workflow column completes.

3. **`typescript-style-mismatch`** — Used explicit return types on obvious functions. Prompt error — user preference wasn't known yet. Now codified in AGENTS.md and memory.

## Pattern Status

- `workflow-steps-skipped`: 2 occurrences (threshold: 3). Watching.
- `plan-not-updated`: 1 occurrence. Watching.
- `typescript-style-mismatch`: 1 occurrence. Resolved via AGENTS.md rule.
