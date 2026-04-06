# Plan: Home Page Dashboard & Frontend Polish

> Spec: [docs/home-and-polish/spec.md](spec.md) · Design: [design-spec.md](design-spec.md)

## Status Dashboard

| Step | Blocks | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| --- | --- | --- | :---: | :---: | :---: | :---: | :---: | :---: |
| [fix-status-bug](steps/fix-status-bug.md) | wire-failure-codes | `92d5f3d` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [add-failure-code-column](steps/add-failure-code-column.md) | wire-failure-codes | `efe75a2` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [wire-failure-codes](steps/wire-failure-codes.md) | failure-message-mapping | `4fa3a38` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [contract-list-api](steps/contract-list-api.md) | dashboard-ui | `bbb3aa3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [dashboard-ui](steps/dashboard-ui.md) | — | `c1dfb6d` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [failure-message-mapping](steps/failure-message-mapping.md) | polish-evaluate-page, polish-detail-page | `0ca98d0` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-color-system](steps/polish-color-system.md) | polish-fairness-tokens, polish-nav-shell | `e1a815b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-nav-shell](steps/polish-nav-shell.md) | — | `c8b7f53` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-fairness-tokens](steps/polish-fairness-tokens.md) | polish-clause-cards | `43f9344` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-evaluate-page](steps/polish-evaluate-page.md) | — | `ccae7ea` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-loading-shimmer](steps/polish-loading-shimmer.md) | — | `df1fa5c`+`0ddb529` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-detail-page](steps/polish-detail-page.md) | — | `d8b653c` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-clause-cards](steps/polish-clause-cards.md) | — | `f4b03dd`+`0ddb529` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| [polish-empty-and-error-states](steps/polish-empty-and-error-states.md) | — | `7464696` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow order per step:** Auto Tests → Verify → Simplify → Review → Understand → Human

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: Proof the code works — real curl, browser automation, Playwright screenshots, DB inspection
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding.

---

## File Map

```
Modify: backend/models.py                          — Add failure_code column to ContractReview
Modify: backend/schemas.py                         — Add failure_code to ReviewOut; add ContractListOut
Modify: backend/services/evaluation.py             — flush→commit fix; set failure_code at each fail site
Modify: backend/routers/contracts.py               — Join latest review in list endpoint
Create: backend/migrations/versions/002_add_failure_code.py — Alembic migration for failure_code
Modify: backend/tests/test_evaluation.py           — Test failure_code is set correctly
Modify: backend/tests/test_contracts.py            — Test list endpoint returns review data
Modify: backend/tests/test_schemas.py              — Test ContractListOut schema

Modify: frontend/app/globals.css                   — Semantic color variables, fadeIn keyframes
Modify: frontend/app/layout.tsx                    — DM Sans font, nav shell
Modify: frontend/app/page.tsx                      — Contract dashboard with empty state
Create: frontend/app/contract-list-types.ts        — Zod schema for contract list items
Modify: frontend/app/evaluate-contract/page.tsx    — Error display, typography, spacing
Modify: frontend/app/evaluate-contract/types.ts    — Add failure_code to review schemas
Create: frontend/app/evaluate-contract/failure-messages.ts — failure_code → user message map
Modify: frontend/app/evaluate-contract/LoadingShimmer.tsx — Stagger animation, fade-in
Modify: frontend/app/evaluate-contract/FileDropZone.tsx — Border color updates
Modify: frontend/app/evaluate-contract/fairness-utils.ts — Semantic color tokens
Modify: frontend/app/contract/[id]/page.tsx        — Typography, blockquote summary, error states
Modify: frontend/app/contract/[id]/ClauseCard.tsx  — Fairness-colored left border
Modify: frontend/app/contract/[id]/ClauseSection.tsx — Spacing, pass fairness to cards
Modify: frontend/app/contract/[id]/ScoreBadge.tsx  — Semantic color tokens
```

---

## Branching Strategy

**Single feature branch** — tightly coupled sequential steps. One branch, commits per step.

---

## Steps

### fix-status-bug
One-line fix: `evaluation.py:99` `flush()` → `commit()` so polling sees "evaluating".
[→ Detailed plan](steps/fix-status-bug.md)

### add-failure-code-column
Add `failure_code` column to `ContractReview` model, Pydantic schema, and Alembic migration.
[→ Detailed plan](steps/add-failure-code-column.md)

### wire-failure-codes
Set `failure_code` at every `_fail_review` call site in `evaluation.py`.
[→ Detailed plan](steps/wire-failure-codes.md)

### contract-list-api
Extend `GET /api/contracts/` to join the latest review per contract and return `ContractListOut[]`.
[→ Detailed plan](steps/contract-list-api.md)

### dashboard-ui
Replace home page hero with contract list + empty state CTA.
[→ Detailed plan](steps/dashboard-ui.md)

### failure-message-mapping
Create `failure_code` → friendly message mapping + update Zod schema with `failure_code` field.
[→ Detailed plan](steps/failure-message-mapping.md)

### polish-color-system
Swap Inter → DM Sans. Add semantic color variables (surface, muted, border, fairness) with dark-mode support. Add fadeIn keyframe.
[→ Detailed plan](steps/polish-color-system.md)

### polish-nav-shell
Add shared nav bar with logo wordmark + "Evaluate Contract" link.
[→ Detailed plan](steps/polish-nav-shell.md)

### polish-fairness-tokens
Migrate fairness badge colors from hardcoded Tailwind to semantic tokens. Updates `fairness-utils.ts` and `ScoreBadge.tsx`.
[→ Detailed plan](steps/polish-fairness-tokens.md)

### polish-evaluate-page
Typography, spacing, border colors, error banner styling on the evaluate-contract page and FileDropZone.
[→ Detailed plan](steps/polish-evaluate-page.md)

### polish-loading-shimmer
Staggered animation delays on shimmer cards + fade-in transition wrapper.
[→ Detailed plan](steps/polish-loading-shimmer.md)

### polish-detail-page
Typography, blockquote summary, muted text, consistent spacing on contract detail page.
[→ Detailed plan](steps/polish-detail-page.md)

### polish-clause-cards
Add fairness-colored left border to `ClauseCard`. Tighten `ClauseSection` spacing.
[→ Detailed plan](steps/polish-clause-cards.md)

### polish-empty-and-error-states
Style failed/not-found/not-a-contract states with centered layouts, alert boxes, and prominent CTAs.
[→ Detailed plan](steps/polish-empty-and-error-states.md)
