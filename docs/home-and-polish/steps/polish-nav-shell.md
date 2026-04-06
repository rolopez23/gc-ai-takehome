# Step: polish-nav-shell

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Adds a minimal shared nav bar across all pages with a logo wordmark linking to `/` and an "Evaluate Contract" link.

## Done When

1. Nav bar renders on all pages with `◆ ContractAI` left and "Evaluate Contract" right
2. Logo links to `/`, evaluate link goes to `/evaluate-contract`
3. `border-b border-border` divider below nav

## Cycles

### nav-component

**Test** — No automated tests (layout/nav component).

**Code** — Add nav to `layout.tsx` (or create `app/Nav.tsx` if cleaner):
- Container: `max-w-2xl mx-auto px-6 h-14 flex items-center justify-between`
- Left: `<Link href="/">` with `◆ ContractAI` text, `font-semibold text-sm`
- Right: `<Link href="/evaluate-contract">` with `Evaluate Contract`, `text-sm text-muted hover:text-foreground`
- Divider: `border-b border-border` on the nav wrapper

**Refactor** — none

**Commit**: `design: add shared nav shell with logo and evaluate action`

---

## Verification

Playwright screenshots:
1. Navigate to `/` — nav bar visible at top with logo and evaluate link
2. Navigate to `/evaluate-contract` — same nav bar
3. Navigate to `/contract/{any-id}` — same nav bar
4. Click logo — navigates to `/`
5. Visually evaluate: does the nav feel minimal and unobtrusive? Is there enough contrast between nav and page content?
