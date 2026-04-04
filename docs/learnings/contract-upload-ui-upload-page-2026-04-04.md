# Learnings: contract-upload-ui / upload-page — 2026-04-04

## Post-Human Additions

2 events logged:

1. **`missing-reset-after-action`** — Spec didn't mention clearing form after submit. User caught it at sign-off. Specification error — /problem-spec stress-test should probe "what happens after the action completes?"

2. **`simplify-not-rerun-after-fix`** — After a review fix introduced new code, simplify was not re-run automatically. User had to request it. The re-run caught a real issue (dead state from mixed controlled/uncontrolled pattern). Skill error — simplify should re-run after any post-simplify code changes.

## Pattern Status

- `workflow-steps-skipped`: 2 occurrences. Watching.
- `missing-reset-after-action`: 1 occurrence. New.
- `simplify-not-rerun-after-fix`: 1 occurrence. New — consider adding to workflow: "re-run simplify after any code changes made during review/walkthrough/sign-off."
