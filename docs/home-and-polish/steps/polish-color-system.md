# Step: polish-color-system

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Swaps Inter → DM Sans font. Adds semantic color CSS variables (surface, muted, border, fairness colors) with proper dark-mode support. Adds `fadeIn` keyframe for later use by shimmer.

## Done When

1. DM Sans loads and renders on all pages
2. `bg-surface`, `text-muted`, `border-border` classes resolve correctly
3. Fairness color tokens (`--fair-fg`, `--unfair-fg`, `--egregious-fg`, etc.) defined for light and dark
4. `@keyframes fadeIn` exists in globals.css

## Cycles

### font-and-variables

**Test** — No automated tests (CSS variables + font swap).

**Code** —

Update `globals.css`:
```css
@import "tailwindcss";

:root {
  --background: #fafaf9;
  --foreground: #1c1917;
  --muted: #78716c;
  --border: #e7e5e4;
  --surface: #ffffff;
  --fair-fg: #15803d;
  --fair-bg: #f0fdf4;
  --fair-border: #bbf7d0;
  --unfair-fg: #a16207;
  --unfair-bg: #fefce8;
  --unfair-border: #fef08a;
  --egregious-fg: #b91c1c;
  --egregious-bg: #fef2f2;
  --egregious-border: #fecaca;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0c0a09;
    --foreground: #e7e5e4;
    --muted: #a8a29e;
    --border: #292524;
    --surface: #1c1917;
    --fair-fg: #4ade80;
    --fair-bg: #052e16;
    --fair-border: #14532d;
    --unfair-fg: #facc15;
    --unfair-bg: #422006;
    --unfair-border: #713f12;
    --egregious-fg: #f87171;
    --egregious-bg: #450a0a;
    --egregious-border: #7f1d1d;
  }
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-muted: var(--muted);
  --color-border: var(--border);
  --color-surface: var(--surface);
  --color-fair-fg: var(--fair-fg);
  --color-fair-bg: var(--fair-bg);
  --color-fair-border: var(--fair-border);
  --color-unfair-fg: var(--unfair-fg);
  --color-unfair-bg: var(--unfair-bg);
  --color-unfair-border: var(--unfair-border);
  --color-egregious-fg: var(--egregious-fg);
  --color-egregious-bg: var(--egregious-bg);
  --color-egregious-border: var(--egregious-border);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: var(--font-sans), Arial, Helvetica, sans-serif;
}
```

Update `layout.tsx`: Replace `Inter` import with `DM_Sans` from `next/font/google`.

**Refactor** — none

**Commit**: `design: swap to DM Sans font and semantic color system`

---

## Verification

Playwright screenshots of all three pages in light + dark mode:
1. Navigate to `/` — confirm DM Sans renders, warm stone background
2. Navigate to `/evaluate-contract` — confirm font and background
3. Toggle dark mode — confirm dark background, no broken/missing variables
4. Visually evaluate: does the warmer palette feel more cohesive than pure black/white?
