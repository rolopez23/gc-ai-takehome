# Spec: M2 — Evaluation Results Display

## Problem Statement

The `/contract/[id]` page is a stub that only shows the raw `overall_fairness` value and summary
string. Users who just uploaded and evaluated a contract land here with no way to understand their
results — which clauses are problematic, how severe each issue is, or what the overall picture
looks like. This page needs to become the primary results experience.

## What We Are Solving

- Display a topline score with the mapped display label (Fair / Unfair / Egregious) and visual
  treatment (color-coded badge)
- Display the evaluation summary string below the topline score
- Group clauses into three sections by fairness tier:
  - **Egregious** (data value: `dealbreaker`)
  - **Unfair** (data value: `non-standard`)
  - **Fair** (data value: `fair`)
- Each section header shows its item count (e.g. "Egregious (2)")
- Each section is collapsible; all start collapsed by default
- When expanded, each clause in a section shows: `section_number`, `clause_type`, `explanation`
- Expanded sections are scroll-constrained to 50vh (half the viewport height)
- Empty-section handling:
  - **Egregious (0)** — non-collapsible placeholder with celebratory icon, text: "No egregious clauses"
  - **Unfair (0)** — non-collapsible placeholder with celebratory icon, text: "No unfair clauses"
  - **Fair (0)** — non-collapsible placeholder with warning icon, text: "No fair clauses found"
- Existing "no evaluation found" fallback remains for missing/expired results
- Navigation link back to the upload/evaluate page (`/evaluate-contract`)
- Display label mapping lives in a shared utility (single source of truth)

## What We Are NOT Solving

- `call_to_action` rendering — out of scope, may be added later
- `purpose` or `market_standard` display per clause — not in this milestone
- Detail drawer/panel on clause click — not in this milestone
- Persistence / surviving page refresh — results are in-memory via context; persistence is M3
- Any changes to the evaluation API, system prompt, or data schema
- Animations or transitions on collapse/expand

## Actors & Triggers

- **Actor**: A user who has just uploaded and evaluated a contract
- **Trigger**: Navigation to `/contract/[id]` after successful evaluation (automatic redirect from
  the evaluate page), or direct visit with a valid UUID in the URL
- **Data source**: `useEvalResult().getResult(id)` returns an `EvalResponse` (discriminated union)
  from the `EvalResultProvider` context. The page narrows this to `EvalSuccess` via the
  `error: null` discriminator.

## Success Criteria

1. Page displays the topline score as a color-coded badge with the mapped label
   (Fair / Unfair / Egregious)
2. Summary string renders below the topline
3. Three sections render in order: Egregious, Unfair, Fair
4. Each non-empty section header shows the correct clause count and is collapsible
5. Expanding a section reveals clause cards showing section_number, clause_type, and explanation
6. Expanded sections are scroll-constrained to 50vh
7. Empty sections render as non-collapsible placeholders with the correct icon treatment
   (celebratory for zero egregious/unfair, warning for zero fair)
8. A navigation link back to `/evaluate-contract` is present
9. "No evaluation found" fallback still works for missing/expired UUIDs
10. All acceptance criteria are covered by tests (RTL + Vitest, 75% line coverage minimum).
    Required test cases:
    - Mixed tiers (clauses across all three fairness levels)
    - All-empty tiers (e.g. contract with only fair clauses — egregious and unfair show placeholders)
    - Missing UUID (fallback renders)
    - Collapse/expand interaction
    - Correct clause count per section header

## Interfaces

### Schemas

**`EvalSuccess`** (read-only, no changes):

| Field             | Type               | Notes                              |
|-------------------|--------------------|------------------------------------|
| `error`           | `null`             | Discriminator for success variant  |
| `overall_fairness`| `FairnessRating`   | `"fair" \| "non-standard" \| "dealbreaker"` |
| `summary`         | `string`           | e.g. "1 dealbreaker, 2 negotiating points, 4 acceptable clauses" |
| `call_to_action`  | `string[]`         | **Not used in this milestone**     |
| `clauses`         | `EvalClause[]`     | Array of evaluated clauses         |

**`EvalClause`** (read-only, no changes):

| Field             | Type             | Used in M2?  |
|-------------------|------------------|--------------|
| `section_number`  | `string`         | Yes          |
| `clause_type`     | `string`         | Yes          |
| `purpose`         | `string`         | No           |
| `fairness`        | `FairnessRating` | Yes (grouping key) |
| `market_standard` | `string`         | No           |
| `explanation`     | `string`         | Yes          |

**Display label mapping** (new — shared utility, single source of truth):

| Data value      | Display label | Badge color |
|-----------------|---------------|-------------|
| `dealbreaker`   | Egregious     | Red         |
| `non-standard`  | Unfair        | Yellow      |
| `fair`          | Fair          | Green       |

### Contracts

No external API calls. This page reads exclusively from the in-memory eval-result context.

### Shared State

- **`EvalResultProvider` context** — shared with the evaluate-contract page which writes results.
  This page only reads. No mutations.

### Existing Code

| File | Role | Changes needed |
|------|------|----------------|
| `frontend/app/contract/[id]/page.tsx` | Results page (stub) | Replace stub with full results UI |
| `frontend/app/evaluate-contract/eval-result-context.tsx` | Context provider | No changes — read-only consumer |
| `frontend/app/evaluate-contract/types.ts` | Type definitions | No changes — consume existing types |

New code to create:

- **Shared utility** for display label mapping (data value → label, color)
- **Components** within `/contract/[id]/` as needed (clause section, clause card, score badge)

## Open Questions

None — all requirements are resolved.
