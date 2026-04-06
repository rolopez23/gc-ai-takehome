# Review: polish-clause-cards

**Date:** 2026-04-05
**Commit:** 1e99460 (cherry-picked from f4b03dd)
**Branch:** agentic-flow/fe-cleanup

## Simplify Assessment

### Duplication with fairness-utils.ts

`FAIRNESS_BORDER` in ClauseCard duplicates the rating-to-border-token mapping that already exists in `fairness-utils.ts` via the `COLORS` export:

- `COLORS.fail` includes `border-egregious-border`
- `COLORS.warning` includes `border-unfair-border`
- `COLORS.pass` includes `border-fair-border`

ClauseCard could call `getFairnessDisplay(fairness).colorClass`, extract only the border token, and avoid the parallel lookup. However, the current `COLORS` strings bundle text + bg + border together, so extracting just the border would require splitting or restructuring. The duplication is minor (3 lines) and self-contained. **Low priority to fix.**

### Type looseness

`fairness` prop is typed as `string` rather than `FairnessRating`. Since the caller (ClauseSection) already has `rating: FairnessRating`, this could safely be `FairnessRating` for better type safety. **Recommended fix.**

## Review Findings

### 1. Does the new required `fairness` prop break other callers?

No. ClauseCard is used in exactly two places:
- `ClauseSection.tsx` line 45 -- updated in this commit, passes `fairness={rating}`
- `clause-section.test.tsx` -- updated in this commit, passes `fairness="dealbreaker"`

No other callers exist. No breakage.

### 2. Is the `?? ''` fallback safe for unknown fairness values?

Functionally safe -- an unknown value produces no border class, so the card renders with only the base `border-l-2` (which uses the default border color). However, if `fairness` were typed as `FairnessRating` instead of `string`, the fallback would be unnecessary since all enum values are covered. The fallback is defensive but masks potential type errors.

### 3. Does `border-border` on ClauseSection match the design spec?

The change from `border-foreground/10` to `border-border` aligns section borders with the Tailwind CSS design token system, using the semantic `--border` CSS variable rather than a hardcoded opacity. This is consistent with standard shadcn/Tailwind conventions and is a quality improvement.

## Summary

| Item | Severity | Action |
|------|----------|--------|
| FAIRNESS_BORDER duplicates fairness-utils COLORS | Low | Track; consolidate if COLORS is restructured |
| `fairness` prop typed as `string` not `FairnessRating` | Medium | Tighten type in a follow-up |
| `?? ''` fallback unnecessary with proper typing | Low | Remove when type is tightened |
| No broken callers | -- | Verified clean |
| `border-border` token change | -- | Correct, matches conventions |
