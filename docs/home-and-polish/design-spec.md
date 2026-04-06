# Design Spec: Home & Polish

## Aesthetic Direction

**Editorial utilitarian** — authoritative, clean, functional. This tool helps people make consequential decisions about contracts. The design should feel like a well-typeset legal brief crossed with a modern SaaS dashboard. No decoration for its own sake. Every visual choice serves information hierarchy.

## Typography

**Replace Inter with a distinctive pairing:**

- **Headings**: `DM Sans` — geometric, slightly warm, professional without being stuffy. Tight tracking for headings. Available on Google Fonts.
- **Body**: `DM Sans` (same family, lighter weights) — maintains cohesion without needing a second font load.

**Three type tiers only:**
| Tier | Usage | Size | Weight |
|------|-------|------|--------|
| **Display** | Page titles, overall verdict | `text-2xl` (24px) | `font-bold` |
| **Label** | Section headers, card titles, badges | `text-sm` (14px) | `font-semibold` |
| **Body** | Explanations, summaries, metadata | `text-sm` (14px) | `font-normal` |

No `text-3xl`, `text-4xl`, or `text-lg` anywhere. The current design uses 4-5 sizes. Flatten to 3.

## Color System

**Extend CSS variables for semantic colors (dark-mode aware):**

```css
:root {
  --background: #fafaf9;          /* stone-50, warmer than pure white */
  --foreground: #1c1917;          /* stone-900 */
  --muted: #78716c;               /* stone-500 */
  --border: #e7e5e4;              /* stone-200 */
  --surface: #ffffff;             /* card backgrounds */

  /* Fairness — muted, professional, not candy-colored */
  --fair-fg: #15803d;             /* green-700 */
  --fair-bg: #f0fdf4;            /* green-50 */
  --fair-border: #bbf7d0;        /* green-200 */

  --unfair-fg: #a16207;          /* yellow-700 */
  --unfair-bg: #fefce8;          /* yellow-50 */
  --unfair-border: #fef08a;      /* yellow-200 */

  --egregious-fg: #b91c1c;       /* red-700 */
  --egregious-bg: #fef2f2;       /* red-50 */
  --egregious-border: #fecaca;   /* red-200 */

  --accent: #1c1917;             /* primary buttons = foreground */
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0c0a09;        /* stone-950 */
    --foreground: #e7e5e4;        /* stone-200 */
    --muted: #a8a29e;             /* stone-400 */
    --border: #292524;            /* stone-800 */
    --surface: #1c1917;           /* stone-900 */

    --fair-fg: #4ade80;           /* green-400 */
    --fair-bg: #052e16;           /* green-950 */
    --fair-border: #14532d;       /* green-900 */

    --unfair-fg: #facc15;         /* yellow-400 */
    --unfair-bg: #422006;         /* yellow-950 */
    --unfair-border: #713f12;     /* yellow-900 */

    --egregious-fg: #f87171;      /* red-400 */
    --egregious-bg: #450a0a;      /* red-950 */
    --egregious-border: #7f1d1d;  /* red-900 */
  }
}
```

Register these in `@theme inline` so Tailwind can use them as `bg-surface`, `text-muted`, `border-border`, etc.

**Update `fairness-utils.ts`** to use the semantic classes:
```
fair:        'text-fair-fg bg-fair-bg border-fair-border'
non-standard:'text-unfair-fg bg-unfair-bg border-unfair-border'
dealbreaker: 'text-egregious-fg bg-egregious-bg border-egregious-border'
```

## Spacing Scale

Standardize on: `1` (4px), `2` (8px), `3` (12px), `4` (16px), `6` (24px), `8` (32px), `12` (48px).

| Context | Token |
|---------|-------|
| Inline gap (icon + text) | `gap-2` |
| Card internal padding | `p-4` |
| Between cards/sections | `space-y-3` |
| Section gap (heading to content) | `mt-4` |
| Page top padding | `pt-12` |
| Page horizontal padding | `px-6` |
| Page max-width | `max-w-2xl` (keep) |

## Shared Page Shell

Add a minimal top bar to `layout.tsx` (or a shared component):

```
┌─────────────────────────────────────────────────────┐
│  ◆ ContractAI                    [Evaluate Contract] │
└─────────────────────────────────────────────────────┘
```

- Left: small logo mark + wordmark. Use `◆` or a simple SVG diamond/shield.
- Right: "Evaluate Contract" link (hidden on evaluate page itself, hidden in empty-state).
- Thin `border-b border-border` divider below.
- The nav is a server component in `layout.tsx`. Pages opt out of showing the evaluate button via a class or conditional.

## Page-by-Page Changes

### 1. Home Page — Contract Dashboard

**With contracts:**
```
┌─────────────────────────────────────────┐
│  Your Contracts                         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ lease_agreement.pdf              │    │
│  │ Completed · Fair         2m ago  │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ vendor_contract.docx             │    │
│  │ Evaluating...            just now│    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ nda_template.txt                 │    │
│  │ Failed                   5m ago  │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

- Each row is a card (`bg-surface border border-border rounded-lg p-4`)
- Top line: contract name, bold, truncated
- Bottom line: status badge (small pill) + fairness badge (if completed) + relative time (right-aligned, muted)
- Entire card is clickable (wraps in `<Link>`)
- Hover: subtle `bg-foreground/[0.03]` shift

**Empty state:**
```
┌─────────────────────────────────────────┐
│                                         │
│           ◆                             │
│   Evaluate your first contract          │
│   Upload a contract to get an AI-       │
│   powered fairness analysis.            │
│                                         │
│   [ Get Started ]                       │
│                                         │
└─────────────────────────────────────────┘
```

- Centered, vertically offset from center (40% from top, not 50%)
- Small diamond icon above heading
- Heading: display tier
- Subtext: body tier, muted
- Button: primary (bg-foreground text-background), rounded-lg, generous padding

### 2. Evaluate Contract Page

Layout tightening:
- Remove page title `text-3xl` → replace with `text-2xl` (display tier)
- FileDropZone: keep as-is but update border color to `border-border` and drag state to accent
- Textarea: update border to `border-border`, focus ring to `ring-1 ring-foreground/20`
- Button: full-width at mobile, auto-width at desktop. `w-full sm:w-auto`
- Error banner: replace bare `<p>` with a styled alert box:
  ```
  ┌─ ⚠ ──────────────────────────────────┐
  │ The evaluation timed out.              │
  │ Please try again.                      │
  └────────────────────────────────────────┘
  ```
  Uses `bg-egregious-bg border border-egregious-border text-egregious-fg rounded-lg p-4`

### 3. Contract Detail Page

**Results view:**
- Overall fairness badge: make it the hero. Larger badge, prominent placement right after title.
- Summary: style as a blockquote — left border accent, slightly larger, muted background.
  ```
  ┌────────────────────────────────────┐
  │ ▎ This contract contains several   │
  │ ▎ non-standard liability clauses...│
  └────────────────────────────────────┘
  ```
  Use `border-l-2 border-foreground/20 pl-4 bg-surface rounded-r-lg py-3 pr-4`
- Call to action list: style as a checklist with muted bullets
- Clause sections: keep expandable pattern but tighten spacing
- ClauseCard: add left border color matching the clause's fairness rating
  ```
  ┌──────────────────────────────────┐
  │ ▎ 3.1 — Liability Cap            │
  │ ▎ Caps total liability at...     │
  └──────────────────────────────────┘
  ```
  `border-l-2 border-{fairness-color}` on each card

**Failed view:**
- Use the same error banner component as evaluate page
- Add "Try again" button (primary) alongside the back link

**Not found / Not a contract:**
- Center vertically (like empty state)
- Muted icon + explanation + CTA

### 4. Loading Shimmer

- Staggered delays: `0ms`, `150ms`, `300ms` on the 3 card placeholders
- Shimmer color: `bg-foreground/[0.04]` (slightly lighter than current `0.06`)
- Add a fade-in wrapper: `opacity-0 animate-[fadeIn_300ms_ease-out_forwards]`
- Define `@keyframes fadeIn { to { opacity: 1 } }` in globals.css

## Implementation Order

These changes touch:
1. `globals.css` — color variables, keyframes
2. `layout.tsx` — font swap (Inter → DM Sans), add nav shell
3. `fairness-utils.ts` — update color classes to semantic tokens
4. `page.tsx` (home) — new dashboard component (separate step, already planned)
5. `evaluate-contract/page.tsx` — typography + spacing + error banner
6. `evaluate-contract/LoadingShimmer.tsx` — shimmer tweaks + stagger
7. `evaluate-contract/FileDropZone.tsx` — border color updates
8. `contract/[id]/page.tsx` — typography + spacing + summary blockquote
9. `contract/[id]/ClauseCard.tsx` — add fairness-colored left border
10. `contract/[id]/ClauseSection.tsx` — spacing tighten
11. `contract/[id]/ScoreBadge.tsx` — use semantic color classes
