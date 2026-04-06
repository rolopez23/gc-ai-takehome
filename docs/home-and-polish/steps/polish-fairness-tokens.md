# Step: polish-fairness-tokens

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Migrates fairness badge colors from hardcoded Tailwind colors (`text-red-600 bg-red-50`) to semantic tokens (`text-egregious-fg bg-egregious-bg`). This makes dark mode work correctly for badges.

## Done When

1. `fairness-utils.ts` COLORS use semantic token classes
2. `ScoreBadge` renders with semantic colors in both light and dark mode
3. Existing fairness-utils and score-badge tests pass (updated assertions)

## Cycles

### migrate-color-classes

**Test** — update existing tests:
- **test_fairness_display_fair_uses_semantic_classes**: Assert `getFairnessDisplay('fair').colorClass` contains `text-fair-fg` (not `text-green-600`)
- **test_fairness_display_nonstd_uses_semantic_classes**: Assert contains `text-unfair-fg`
- **test_fairness_display_dealbreaker_uses_semantic_classes**: Assert contains `text-egregious-fg`

**Code** — Update `fairness-utils.ts`:
```typescript
export const COLORS = {
  fail: 'text-egregious-fg bg-egregious-bg border-egregious-border',
  warning: 'text-unfair-fg bg-unfair-bg border-unfair-border',
  pass: 'text-fair-fg bg-fair-bg border-fair-border',
} as const;
```

`ScoreBadge.tsx` needs no changes — it already uses `getFairnessDisplay`.

**Refactor** — none

**Commit**: `design: migrate fairness badges to semantic color tokens`

---

## Verification

Playwright screenshots:
1. Navigate to a completed contract detail page
2. Screenshot — confirm fairness badges render with correct colors
3. Toggle dark mode — confirm badges are readable (not washed-out `bg-red-50` on dark bg)
4. Visually evaluate: do the muted professional tones look better than the candy colors?
