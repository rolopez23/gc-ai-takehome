# Review: polish-loading-shimmer

**Date:** 2026-04-05
**Commit:** 5a22d46

## Critical: animationDelay is a no-op

The `style={{ animationDelay: \`${i * 150}ms\` }}` on card wrappers has no visual effect. The card divs themselves have no CSS animation. The `animate-pulse` lives on inner `ShimmerBar` components. CSS `animation-delay` does not inherit or cascade to children.

**To actually stagger the cards**, one of these approaches is needed:
1. Add an `animate-pulse` (or a custom stagger animation) to the card div itself, so `animationDelay` has something to delay.
2. Pass the delay down to each `ShimmerBar` as an inline style, offsetting each bar's pulse by the card's base delay.
3. Remove `animationDelay` entirely if a uniform pulse is acceptable -- the fade-in already provides enough visual polish.

The existing test only asserts the attribute exists, not the visual behavior, so it masks this issue.

## Simplify findings

- **Dead `space-y-6`**: The outer `div.space-y-6` now has exactly one child (the fade-in wrapper). The class does nothing. Could remove it, or move `space-y-6` inside the fade-in wrapper and drop the `mt-6` on each child. The `mt-6` approach works but is more repetitive.
- **Shimmer bar opacity**: `bg-foreground/[0.04]` is very subtle. On some monitors this may be nearly invisible. Worth a visual check on different displays. Not a bug, just a callout.

## What's correct

- Fade-in wrapper is well-implemented: `opacity-0` + `animate-[fadeIn_300ms_ease-out_forwards]` with the keyframe defined in `globals.css`.
- `data-testid="shimmer-card"` additions are clean and useful for testing.
- Key change from `[1,2,3]` to `[0,1,2]` is fine -- no stability concern.
- All tests pass.

## Verdict

**Needs fix**: The `animationDelay` stagger is dead code. Either make it functional or remove it. Low severity (cosmetic), but the intent of the commit is to add stagger, and it does not deliver that.

**Optional cleanup**: Remove `space-y-6` from outer div.
