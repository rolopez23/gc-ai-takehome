# Review: polish-detail-page

**Date**: 2026-04-05
**Verdict**: PASS — no blocking issues

## Simplify

- No dead code found. All constants (`PAGE_CONTAINER`, `PAGE_TITLE`, `BACK_LINK`) are used.
- `getFailureMessage` import is clean — the function handles null/undefined gracefully with a fallback to `FAILURE_MESSAGES.unknown`.
- Blockquote markup is concise and not duplicated elsewhere.

## Correctness

| Check | Result |
|---|---|
| `getFailureMessage` import resolves | PASS — imported from `@/app/evaluate-contract/failure-messages` (line 11), file exists at that path |
| `getFailureMessage` handles null `failure_code` | PASS — function signature accepts `string | null | undefined`, returns unknown fallback |
| All `text-foreground/60` and `/70` replaced with `text-muted` in this file | PASS — zero instances of `text-foreground/60` or `text-foreground/70` in `page.tsx` |
| `BACK_LINK` uses `text-muted` | PASS — line 17 |

## Observations

1. **Residual `text-foreground/70` in ClauseCard.tsx**: Line 13 of `ClauseCard.tsx` still uses `text-foreground/70` for the `EXPLANATION` constant. This is outside this step's scope but is a consistency gap.
2. **Residual `text-foreground/60` in other files**: `FileDropZone.tsx` (lines 84, 91, 109) and `LoadingShimmer.tsx` (line 15) still use `text-foreground/60`. Also out of scope but noted for follow-up.

## Risks

None. All changes are CSS-only or use an existing tested utility function.
