# Verify: polish-loading-shimmer

**Date:** 2026-04-05
**Commit:** 5a22d46 (cherry-picked from df1fa5c)

## Test results

All 7 loading-shimmer tests pass:

- shows shimmer when submitting
- disables button when submitting
- sends FormData to backend upload endpoint
- shimmer cards have staggered delay
- shimmer has fade-in
- hides shimmer on failed evaluation
- shows loading shimmer while pending (contract-results-page suite)

## Fade-in verification

The `fadeIn` keyframe is defined in `globals.css` (lines 56-59). The wrapper's `animate-[fadeIn_300ms_ease-out_forwards]` class correctly references it. The `opacity-0` initial state plus `forwards` fill mode means the content fades from 0 to 1 over 300ms, then stays visible. This works correctly.

## animationDelay concern -- LIKELY NO-OP

**The `animationDelay` on card wrapper divs does NOT stagger the child `animate-pulse` animations.** The card div itself has no `animation` property -- `animationDelay` only affects animations on the element it is set on. The `animate-pulse` class is on individual `ShimmerBar` children, not the card wrapper. CSS animation-delay does not cascade to children.

The test (`shimmer cards have staggered delay`) passes because it only checks that the `style.animationDelay` attribute is present on the DOM element -- it does not verify that any visual stagger occurs.

**Verdict: The stagger is a no-op visually.** The shimmer bars inside all three cards pulse in sync.

## space-y-6 to mt-6

The outer div retains `space-y-6`, but since it now has only one child (the fade-in wrapper), `space-y-6` is inert. Inside the wrapper, children use explicit `mt-6`. This produces the same 1.5rem gap as before. No visual regression, though the outer `space-y-6` is now dead code.

## Key stability

Changing from `[1,2,3]` to `[0,1,2]` has no key stability issue -- React keys are still unique integers within the same list.
