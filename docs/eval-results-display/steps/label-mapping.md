# Step: label-mapping

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

A shared utility that maps `FairnessRating` data values (`fair`, `non-standard`, `dealbreaker`)
to their user-facing display labels (`Fair`, `Unfair`, `Egregious`), badge color classes, and
section rendering order. This is the single source of truth consumed by all UI components in M2.

## Done When

`fairness-utils.ts` exports functions/constants that map each `FairnessRating` to its display
label and color, and all mappings are covered by unit tests.

## Cycles

### mapping-returns-correct-labels

**Test** — write these tests in `frontend/__tests__/fairness-utils.test.ts` and confirm they fail:
- **maps dealbreaker to Egregious**: `getFairnessDisplay('dealbreaker').label` equals `'Egregious'`
- **maps non-standard to Unfair**: `getFairnessDisplay('non-standard').label` equals `'Unfair'`
- **maps fair to Fair**: `getFairnessDisplay('fair').label` equals `'Fair'`

**Code** — Create `frontend/app/evaluate-contract/fairness-utils.ts`. Export a
`getFairnessDisplay(rating: FairnessRating)` function that returns
`{ label: string, colorClass: string }`. Use a simple record lookup:

```typescript
const FAIRNESS_DISPLAY: Record<FairnessRating, { label: string; colorClass: string }> = {
  dealbreaker: { label: 'Egregious', colorClass: 'text-red-600 bg-red-50 border-red-200' },
  'non-standard': { label: 'Unfair', colorClass: 'text-yellow-600 bg-yellow-50 border-yellow-200' },
  fair: { label: 'Fair', colorClass: 'text-green-600 bg-green-50 border-green-200' },
};
```

**Refactor** — none

**Commit**: `Add fairness display label mapping utility`

---

### section-order-constant

**Test** — add to the same test file:
- **FAIRNESS_SECTION_ORDER has three entries in severity order**: assert
  `FAIRNESS_SECTION_ORDER` equals `['dealbreaker', 'non-standard', 'fair']`

**Code** — Export `FAIRNESS_SECTION_ORDER: FairnessRating[]` from `fairness-utils.ts`.

**Refactor** — none

**Commit**: `Add fairness section order constant`

---

## LLM Verification

**N/A** — pure utility with no external surface. Unit tests are the verification.
