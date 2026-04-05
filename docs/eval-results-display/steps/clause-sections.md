# Step: clause-sections

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Three collapsible sections on the results page — Egregious, Unfair, Fair — each grouping
clauses by fairness tier. Sections show clause counts in headers, expand to reveal clause
cards (section_number, clause_type, explanation), are scroll-constrained to 50vh, and show
appropriate empty-state placeholders when a tier has zero clauses.

## Done When

All section states are tested: populated sections collapse/expand with correct counts, clause
cards display the right fields, expanded sections are scroll-constrained, and empty sections
show placeholders with the correct icon treatment.

## Dependencies

- `fairness-utils.ts` (label-mapping step) — display labels, colors, section order
- `ScoreBadge` and page structure (topline-score step) — page exists and renders

## Cycles

### clause-card-renders-fields

**Test** — write in `frontend/__tests__/clause-section.test.tsx`:
- **renders section_number, clause_type, and explanation**: render `<ClauseCard clause={testClause} />`
  with a fixture clause, assert all three field values are visible in the document

**Code** — Create `frontend/app/contract/[id]/ClauseCard.tsx`. A presentational component that
takes `{ clause: EvalClause }` and renders `section_number`, `clause_type`, and `explanation`.

**Refactor** — none

**Commit**: `Add ClauseCard component displaying clause fields`

---

### collapsible-section-header-with-count

**Test** — add to `frontend/__tests__/clause-section.test.tsx`:
- **renders section header with label and count**: render
  `<ClauseSection rating="dealbreaker" clauses={[clause1, clause2]} />`,
  assert header text contains "Egregious" and "(2)"
- **starts collapsed — clauses not visible**: assert clause explanation text is not in the document

**Code** — Create `frontend/app/contract/[id]/ClauseSection.tsx`. Takes
`{ rating: FairnessRating, clauses: EvalClause[] }`. Renders a clickable header with the
display label and count. Uses local `useState(false)` for expanded state. When collapsed,
clause cards are not rendered.

**Refactor** — none

**Commit**: `Add collapsible ClauseSection with header count`

---

### expand-reveals-clause-cards

**Test** — add to the same file:
- **clicking header expands section and shows clauses**: render a `ClauseSection` with two clauses,
  click the header button, assert both clause explanations are now visible
- **clicking header again collapses section**: click header a second time, assert clauses are
  no longer visible

**Code** — Toggle the expanded state on header click. When expanded, render `ClauseCard` for
each clause in the `clauses` array.

**Refactor** — none

**Commit**: `Add expand/collapse interaction to ClauseSection`

---

### scroll-constraint-on-expanded-section

**Test** — add to the same file:
- **expanded section container has max-height 50vh and overflow-y auto**: render an expanded
  `ClauseSection`, assert the clause list container has `max-h-[50vh]` and `overflow-y-auto`
  classes (or equivalent style check)

**Code** — Wrap the clause card list in a `div` with `className="max-h-[50vh] overflow-y-auto"`.

**Refactor** — none

**Commit**: `Add 50vh scroll constraint to expanded clause sections`

---

### empty-section-celebratory-placeholder

**Test** — add to the same file:
- **renders celebratory placeholder for empty egregious section**: render
  `<ClauseSection rating="dealbreaker" clauses={[]} />`, assert text "No egregious clauses"
  is visible, section is not collapsible (no button role in header)
- **renders celebratory placeholder for empty unfair section**: render
  `<ClauseSection rating="non-standard" clauses={[]} />`, assert text "No unfair clauses"

**Code** — In `ClauseSection`, when `clauses.length === 0` and rating is `dealbreaker` or
`non-standard`: render a static (non-collapsible) placeholder with a celebratory icon
(e.g. a check-circle or party icon via unicode/SVG) and the "No {label} clauses" text.

**Refactor** — none

**Commit**: `Add celebratory empty-state placeholder for egregious and unfair sections`

---

### empty-section-warning-placeholder

**Test** — add to the same file:
- **renders warning placeholder for empty fair section**: render
  `<ClauseSection rating="fair" clauses={[]} />`, assert text "No fair clauses found"
  is visible with a warning icon treatment

**Code** — In `ClauseSection`, when `clauses.length === 0` and rating is `fair`: render a
static placeholder with a warning icon and "No fair clauses found" text.

**Refactor** — Extract the empty-state rendering into a clean conditional at the top of
`ClauseSection` (early return pattern).

**Commit**: `Add warning empty-state placeholder for fair section`

---

### wire-sections-into-page

**Test** — add to `frontend/__tests__/contract-results-page.test.tsx`:
- **renders three sections in order — Egregious, Unfair, Fair**: mock result with clauses
  across all three tiers, assert all three section headers are present and in DOM order
- **shows correct clause count per section**: mock result with 1 dealbreaker, 2 non-standard,
  3 fair clauses, assert headers show "(1)", "(2)", "(3)" respectively
- **shows placeholders for empty tiers**: mock result with only fair clauses, assert
  "No egregious clauses" and "No unfair clauses" placeholders are visible

**Code** — In `page.tsx`, group `result.clauses` by `fairness` tier. Iterate
`FAIRNESS_SECTION_ORDER` and render a `<ClauseSection>` for each tier, passing the filtered
clauses.

**Refactor** — Extract clause grouping into a helper function if it improves readability.

**Commit**: `Wire clause sections into contract results page`

---

## LLM Verification

Navigate to `/contract/<test-uuid>` after evaluating a contract. Verify:
- Three sections render in order: Egregious, Unfair, Fair
- Section headers show correct counts
- Clicking a populated section header expands to show clause cards
- Expanded sections scroll when content exceeds half the viewport
- Empty sections show placeholders (celebratory for egregious/unfair, warning for fair)
