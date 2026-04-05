# Frontend Cleanup

Sub-skill of `/simplify`. Run this **automatically** when the diff touches React components
(`.tsx` files that export JSX). These checks supplement the main simplify pass — they are
specific to React/frontend code and catch patterns that generic code review misses.

## What to Check

### 1. Component Extraction

A component doing too much is the frontend equivalent of a function doing too much.

- **Route between variants**: If a component has an early return for an empty/error state and
  a main render path, extract each into its own named component. The parent becomes a stateless
  router (e.g., `ClauseSection` → `NoClauses` | `ExpandableClauses`).
- **Move state down**: If a parent holds state only one child uses, extract that child as a
  component that owns its own state. The parent should not hold state it doesn't read.
- **Presentational vs stateful**: Presentational components (no hooks, pure props → JSX) should
  be clearly separated from stateful ones. If a component has both, consider splitting.

### 2. Semantic HTML

React defaults to `<div>` and `<span>` for everything. Push toward semantic elements:

| Instead of | Use | When |
|---|---|---|
| `<div>` wrapping a list of items | `<ul>` / `<ol>` + `<li>` | Rendering an array of similar items |
| `<div>` for a titled section | `<section>` with heading | Grouping related content with a label |
| `<div>` for standalone content | `<article>` | Content that makes sense on its own (e.g., a full evaluation result) |
| `<div>` + `<span>` for a title | `<h2>`–`<h6>` | Hierarchical headings within a page |
| `<div>` for a card | `<div>` is fine | When the content needs its parent section for context |

**Key judgment call**: `<article>` means standalone — content that could be syndicated or
understood without its parent. A clause card inside a section is not an article. An entire
evaluation result is.

### 3. Accessibility Attributes

Check for missing ARIA that a screen reader would need:

- **`aria-label`** on `<section>` elements — e.g., `aria-label="Unfair clauses"`
- **`aria-expanded`** on toggle buttons that show/hide content
- **`role="status"`** on loading indicators
- **`aria-busy`** on containers that are loading
- **`sr-only`** text for visual-only indicators (icons, color-coded badges)

### 4. Readable Class Names

Long Tailwind class strings inline in JSX hurt readability. Extract to named constants when:

- The class string is **longer than ~60 characters**
- The same class string appears in **2+ places** (also a DRY issue)
- The class string represents a **reusable concept** (e.g., section border, card layout)

Name the constant after what it represents, not what it looks like:

```typescript
// Good
const SECTION_HEADER = 'flex w-full items-center justify-between rounded-lg border ...';
const BADGE_STYLING = 'inline-block rounded-full border px-3 py-1 text-sm font-semibold';

// Bad
const FLEX_ROUNDED_BORDER = '...';
```

Short utility classes (`mt-4`, `text-sm`, `font-bold`) are fine inline — don't over-extract.

### 5. Data Transformations

Prefer declarative over imperative when transforming data for rendering:

| Pattern | Use | Instead of |
|---|---|---|
| Array → grouped object | `reduce` | `for` loop with manual accumulator |
| Array → filtered subset | `filter` | `for` loop with `if` + `push` |
| Array → mapped output | `map` | `for` loop with `push` |

The `reduce` / `filter` / `map` versions read as transformations (what), not procedures (how).
Performance is equivalent for UI-scale data.

### 6. Color and Style Constants

When colors or styles map to domain concepts (severity, status, state), use semantically
named constants:

```typescript
// Good — names describe meaning
const COLORS = {
  fail: 'text-red-600 bg-red-50 border-red-200',
  warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  pass: 'text-green-600 bg-green-50 border-green-200',
} as const;

// Bad — names describe appearance
const RED_CLASSES = 'text-red-600 bg-red-50 border-red-200';
```

### 7. Test Assertions on Styles

Tests should assert against semantic names, roles, or behavior — not raw CSS class names:

- Assert `COLORS.fail` not `'text-red-600'`
- Assert `getByRole('list')` not `closest('[class*="max-h-"]')`
- Assert `aria-expanded` state not presence of a CSS class

## Output

For each finding, state:
- Which category (1–7) it falls under
- The specific file and component
- The fix (apply directly if clear, suggest if uncertain)

If no React-specific issues are found, output: "Frontend cleanup: nothing to flag."
