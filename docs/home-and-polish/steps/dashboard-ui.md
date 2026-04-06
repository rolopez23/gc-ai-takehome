# Step: dashboard-ui

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Replaces the static home page hero with a contract dashboard. Fetches `GET /api/contracts/` and renders a list showing name, review status, and fairness rating per contract. Each row links to `/contract/[uuid]`. Empty state shows a prominent CTA to evaluate the first contract.

## Done When

1. Home page fetches and displays contract list from backend
2. Each row shows contract name, status badge, and fairness badge (if completed)
3. Clicking a row navigates to `/contract/{id}`
4. Empty state shows "Evaluate your first contract" CTA linking to `/evaluate-contract`
5. Standard evaluate button hidden in empty state (CTA replaces it)

## Cycles

### contract-list-types

**Test** — write these tests and confirm they fail:
- **test_contract_list_item_schema_parses**: Parse a valid contract list JSON object through `ContractListItemSchema`. Assert all fields including nullable `review_status`, `overall_fairness`, `failure_code`. · setup: none
- **test_contract_list_item_schema_rejects_invalid**: Pass an object missing `id`. Assert Zod throws. · setup: none

**Code** — Create `frontend/app/contract-list-types.ts`:
```typescript
import { z } from 'zod';
import { FairnessRatingSchema } from '@/app/evaluate-contract/types';

export const ContractListItemSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  upload_type: z.string(),
  created_at: z.string(),
  review_status: z.string().nullable(),
  overall_fairness: FairnessRatingSchema.nullable(),
  failure_code: z.string().nullable(),
});

export type ContractListItem = z.infer<typeof ContractListItemSchema>;
```

**Refactor** — none

**Commit**: `add Zod schema for contract list items`

---

### dashboard-empty-state

**Test** �� write these tests and confirm they fail:
- **test_dashboard_shows_empty_state**: Mock fetch to return `[]`. Render home page. Assert "Evaluate your first contract" CTA is visible. Assert CTA links to `/evaluate-contract`. · setup: mock fetch
- **test_dashboard_empty_state_hides_evaluate_button**: Mock fetch to return `[]`. Render home page. Assert no secondary "Evaluate" nav link exists. · setup: mock fetch

**Code** — Rewrite `frontend/app/page.tsx` as a client component that fetches `/api/contracts/` on mount. When list is empty, render an empty-state card with prominent CTA button linking to `/evaluate-contract`.

**Refactor** — none

**Commit**: `add dashboard empty state with evaluate CTA`

---

### dashboard-contract-list

**Test** — write these tests and confirm they fail:
- **test_dashboard_renders_contract_rows**: Mock fetch to return 2 contracts (one completed/fair, one pending). Assert both names render. Assert fairness badge shows for completed contract. Assert status shows for pending contract. · setup: mock fetch with fixture data
- **test_dashboard_row_links_to_contract**: Mock fetch to return 1 contract. Assert the row is wrapped in a link to `/contract/{id}`. · setup: mock fetch
- **test_dashboard_shows_failed_status**: Mock fetch to return 1 failed contract with `failure_code="timeout"`. Assert row shows "Failed" status styling. · setup: mock fetch

**Code** — Add the contract list rendering to `page.tsx`. Each row is a `<Link>` to `/contract/{id}` showing:
- Contract name (truncated if long)
- Status badge (pending/evaluating/completed/failed)
- Fairness badge (using existing `ScoreBadge` or similar) — only when status is completed and overall_fairness is not null
- `created_at` formatted as relative time or short date

Add an "Evaluate Contract" button/link in the header that navigates to `/evaluate-contract`.

**Refactor** — Extract row component if the JSX gets long.

**Commit**: `render contract list on dashboard with status and fairness badges`

---

## Verification

```bash
# 1. Run frontend tests
cd frontend && npm run test

# 2. Manual: start both servers, visit home page
# With contracts: see list with names, status badges, fairness ratings
# Click a row: navigates to /contract/{id}
# With no contracts: see "Evaluate your first contract" CTA
# Click CTA: navigates to /evaluate-contract
```
