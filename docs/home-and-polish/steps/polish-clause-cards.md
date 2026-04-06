# Step: polish-clause-cards

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Adds a fairness-colored left border to each `ClauseCard` so you can see at a glance which rating a clause has. Tightens `ClauseSection` border to use semantic token.

## Done When

1. Each `ClauseCard` has a `border-l-2` with color matching its fairness rating
2. `ClauseSection` border uses `border-border` token
3. Fairness rating is passed from section to card

## Cycles

### fairness-left-border

**Test** — update `clause-section.test.tsx`:
- **test_clause_card_has_fairness_border**: Render a `ClauseSection` with `rating="fair"` and one clause. Expand it. Assert the rendered card has class containing `border-fair-border`.

**Code** —

Update `ClauseCard.tsx`:
- Accept `fairness: string` prop
- Add border class lookup:
  ```typescript
  const FAIRNESS_BORDER: Record<string, string> = {
    fair: 'border-fair-border',
    'non-standard': 'border-unfair-border',
    dealbreaker: 'border-egregious-border',
  };
  ```
- Apply `border-l-2 ${FAIRNESS_BORDER[fairness] ?? ''}` to the card div

Update `ClauseSection.tsx`:
- Pass `fairness={rating}` (the section's rating) to each `ClauseCard`
- Section border: `border-foreground/10` → `border-border`

**Refactor** — none

**Commit**: `design: add fairness-colored left border to clause cards`

---

## Verification

Playwright screenshots:
1. Navigate to a completed contract with clauses in multiple fairness categories
2. Expand all sections — screenshot
3. Confirm: fair cards have green-ish left border, unfair have yellow-ish, egregious have red-ish
4. Dark mode — confirm border colors are visible
5. Visually evaluate: does the left border add useful information without clutter?
