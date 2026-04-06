# Review: polish-fairness-tokens

**Date:** 2026-04-05
**Commit:** 9e65bd3 (cherry-picked from 43f9344)
**Branch:** agentic-flow/fe-cleanup

## Diff summary

3-line change in `fairness-utils.ts` replacing hardcoded Tailwind color classes with semantic tokens:

- `fail`: `text-red-600 bg-red-50 border-red-200` -> `text-egregious-fg bg-egregious-bg border-egregious-border`
- `warning`: `text-yellow-600 bg-yellow-50 border-yellow-200` -> `text-unfair-fg bg-unfair-bg border-unfair-border`
- `pass`: `text-green-600 bg-green-50 border-green-200` -> `text-fair-fg bg-fair-bg border-fair-border`

## Review checklist

### Do the new class names match CSS variables in globals.css?

YES. `globals.css` defines all 9 CSS custom properties (`--fair-fg`, `--fair-bg`, `--fair-border`, etc.) for both light and dark mode, and maps them to Tailwind via `--color-*` aliases at lines 45-53. The token names in `fairness-utils.ts` map 1:1.

### Does ScoreBadge pick up new tokens without changes?

YES. `ScoreBadge.tsx` calls `getFairnessDisplay(rating)` and spreads the returned `colorClass` into the className. It references the `COLORS` object indirectly through the display map, so the token change flows through automatically.

### Any tests asserting on old color classes?

NO. Both `score-badge.test.tsx` and `fairness-utils.test.ts` assert against the imported `COLORS` constant (e.g., `COLORS.fail`), not hardcoded strings. `clause-section.test.tsx` already asserts `border-egregious-border`. Grep for old color strings across `__tests__/` returns zero matches.

## Simplify

Nothing to simplify. This is a 3-line constant swap with no logic changes.

## Issues found

None.

## Verdict

APPROVED. Clean, minimal change. Token naming is consistent, CSS definitions cover light/dark, tests are resilient to the swap.
