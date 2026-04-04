# Learnings: contract-upload-ui / file-drop-zone — 2026-04-04

## Post-Human Additions

3 events logged:

1. **`rtl-query-antipattern`** — Used `document.querySelector` instead of RTL accessibility queries. Skill error — simplify/review should catch this.
2. **`unnecessary-type-cast`** — Littered tests with `as HTMLInputElement` casts that weren't needed. Skill error — simplify should flag unnecessary casts.
3. **`unnecessary-comments`** — Comments explaining what code already shows. Context error — walkthrough questions shouldn't match existing comments.

## Pattern Status

- `workflow-steps-skipped`: 2 occurrences. Watching.
- `rtl-query-antipattern`: 1 occurrence. New — codified in FrontendTesting.md.
- `unnecessary-type-cast`: 1 occurrence. New — codified in FrontendTesting.md.
- `unnecessary-comments`: 1 occurrence. Watching.
