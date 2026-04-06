# Step: polish-loading-shimmer

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Adds staggered animation delays to shimmer clause card placeholders and a fade-in transition on mount.

## Done When

1. Three shimmer cards animate with delays of 0ms, 150ms, 300ms
2. Shimmer wrapper fades in over 300ms on mount
3. Shimmer bar color slightly lighter (`bg-foreground/[0.04]`)

## Cycles

### stagger-and-fade

**Test** — update `loading-shimmer.test.tsx`:
- **test_shimmer_cards_have_staggered_delay**: Render `LoadingShimmer`. Query `[data-testid="shimmer-card"]` elements. Assert 3 elements with `animationDelay` of `0ms`, `150ms`, `300ms`.
- **test_shimmer_has_fade_in_class**: Render `LoadingShimmer`. Assert wrapper has `animate-[fadeIn_300ms_ease-out_forwards]` class.

**Code** — Update `LoadingShimmer.tsx`:
- Wrap entire shimmer in `<div className="opacity-0 animate-[fadeIn_300ms_ease-out_forwards]">`
- Change shimmer bar color: `bg-foreground/[0.06]` → `bg-foreground/[0.04]`
- Add `data-testid="shimmer-card"` and `style={{ animationDelay: \`${(i - 1) * 150}ms\` }}` to each card div (note: the map uses `i` starting from 1)

**Refactor** — none

**Commit**: `design: staggered shimmer cards and fade-in transition`

---

## Verification

Playwright screenshots:
1. Navigate to `/evaluate-contract`, upload a file to trigger loading state
2. Screenshot the shimmer — confirm cards visible with stagger effect
3. Visually evaluate: does the stagger create a pleasant ripple? Does the fade-in feel smooth?
