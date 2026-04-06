# Review: polish-color-system

**Date**: 2026-04-05
**Commit**: d274847
**Reviewers**: correctness, exhaustive, adversarial (merged)

## Fairness Tokens Completeness

All 9 fairness tokens (fair/unfair/egregious x fg/bg/border) have both light and dark values. Confirmed by line-by-line comparison of `:root` (lines 6-17) and `@media (prefers-color-scheme: dark)` (lines 21-36) blocks.

| Token | Light | Dark |
|-------|-------|------|
| --fair-fg | #15803d | #4ade80 |
| --fair-bg | #f0fdf4 | #052e16 |
| --fair-border | #bbf7d0 | #14532d |
| --unfair-fg | #a16207 | #facc15 |
| --unfair-bg | #fefce8 | #422006 |
| --unfair-border | #fef08a | #713f12 |
| --egregious-fg | #b91c1c | #f87171 |
| --egregious-bg | #fef2f2 | #450a0a |
| --egregious-border | #fecaca | #7f1d1d |

## @theme inline Completeness

Every `:root` variable is registered in `@theme inline`. 14 variables in `:root`, 14 `--color-*` entries in `@theme inline`. No orphans, no gaps.

## DM Sans Import

Correct. `DM_Sans` imported from `next/font/google`, configured with `subsets: ["latin"]`, `variable: "--font-sans"`. Applied to `<body>` via `dmSans.variable`. Font-family fallback in `globals.css` references `var(--font-sans)` with Arial/Helvetica/sans-serif fallbacks.

## Accessibility: Background Contrast

- Light: foreground #1c1917 on background #fafaf9 = contrast ratio ~18.2:1. Exceeds WCAG AAA (7:1).
- Light: muted #78716c on background #fafaf9 = contrast ratio ~4.6:1. Passes WCAG AA (4.5:1) for normal text. Just barely -- worth monitoring.
- Dark: foreground #e7e5e4 on background #0c0a09 = contrast ratio ~16.8:1. Exceeds WCAG AAA.
- Dark: muted #a8a29e on background #0c0a09 = contrast ratio ~8.5:1. Exceeds WCAG AAA.

## Findings

| # | Severity | Finding |
|---|----------|---------|
| 1 | **info** | Design spec defines `--accent: #1c1917` but it was intentionally omitted from implementation. No code references `--accent` anywhere, so this is not a gap -- it can be added later if needed. |
| 2 | **info** | Muted text on light background (#78716c on #fafaf9) has a contrast ratio of ~4.6:1. Passes AA but is borderline. If muted text is used at `text-xs` or smaller, it would need 4.5:1 minimum (large text threshold is 3:1). Current usage is `text-sm`, so this is fine. |
| 3 | **info** | The `fadeIn` keyframe is defined but not yet referenced by any component. Expected -- it is scaffolding for the loading-shimmer step. |

## Simplify

No simplification opportunities. The diff is minimal and focused: 14 variables added to `:root`, mirrored in dark mode, registered in `@theme inline`, one font swap. No dead code, no duplication, no over-abstraction.

## Verdict

**PASS** -- no blocking issues. Implementation matches the design spec exactly (minus the intentionally deferred `--accent`). All tokens are complete and symmetric between light and dark modes.
