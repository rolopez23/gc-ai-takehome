# Plan: M2 — Evaluation Results Display

> Spec: [docs/eval-results-display/spec.md](spec.md)

## Status Dashboard

| Step                                                      | Blocks              | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| --------------------------------------------------------- | -------------------- | --------------- | :--------: | :----: | :------: | :----: | :--------: | :---: |
| [label-mapping](steps/label-mapping.md)                   | topline-score, clause-sections | aa4638b |     ✅     |   ➖   |    ✅    |   ✅   |     ✅     |  ✅   |
| [topline-score](steps/topline-score.md)                   | clause-sections      | 68b09ac         |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |
| [clause-sections](steps/clause-sections.md)               | —                    | f2356ad         |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow order per step:** Auto Tests → Verify → Simplify → Review → Understand → Human

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: E2E check — real curl or browser automation against a live system; ➖ if no external surface
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High in the
  understanding assessment. Run with the step's commit range (before/after). Low on any file → ❌,
  follow up on low areas before sign-off
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding. Do not mark Human ✅ while any
prior column is ❌ without explicit user instruction.

---

## File Map

```
Create:  frontend/app/evaluate-contract/fairness-utils.ts       — Display label mapping utility (single source of truth)
Modify:  frontend/app/contract/[id]/page.tsx                    — Replace stub with full results page
Create:  frontend/app/contract/[id]/ScoreBadge.tsx              — Topline score badge component
Create:  frontend/app/contract/[id]/ClauseSection.tsx           — Collapsible section with count header + empty-state
Create:  frontend/app/contract/[id]/ClauseCard.tsx              — Single clause display (section_number, clause_type, explanation)
Test:    frontend/__tests__/fairness-utils.test.ts
Test:    frontend/__tests__/score-badge.test.tsx
Test:    frontend/__tests__/clause-section.test.tsx
Test:    frontend/__tests__/contract-results-page.test.tsx
```

---

## Branching Strategy

**Single feature branch.** The three steps are sequential and tightly coupled — each builds on
the previous. One branch with commits per TDD cycle keeps the history clean and avoids merge
overhead for a feature this size.

---

## Steps

### label-mapping

Pure utility that maps `FairnessRating` data values to display labels, badge colors (Tailwind
classes), and section order. No UI, no dependencies. Done when the mapping is tested and exported.

[→ Detailed plan](steps/label-mapping.md)

### topline-score

Score badge and summary rendering on the contract page. Reads `overall_fairness` and `summary`
from the eval context and displays the mapped label in a color-coded badge with the summary below.
Includes the back-to-upload navigation link. Done when the page renders topline + summary + nav
link for all three fairness levels.

[→ Detailed plan](steps/topline-score.md)

### clause-sections

Three collapsible sections grouping clauses by fairness tier. Each section header shows the
display label and count. Expanding reveals clause cards (section_number, clause_type, explanation)
scroll-constrained to 50vh. Empty sections render as non-collapsible placeholders with the
appropriate icon. Done when all section states (populated, empty, collapse/expand) are tested.

[→ Detailed plan](steps/clause-sections.md)
