# Review: dashboard-ui (2026-04-05)

## Simplify

- **timeAgo** is only used in `page.tsx` (confirmed via search). No duplication.
- **Fetch on every mount with no caching:** Acceptable for now. The contract list is small and the page is not a high-traffic view. SWR/React Query would be overkill at this stage.
- **Code quality:** Clean separation -- `StatusDisplay` extracted as its own component. `ContractListItemSchema` in a dedicated file. No unnecessary complexity.

## Review Findings

### PASS

| Item | Status |
|---|---|
| Empty state CTA links to `/evaluate-contract` | PASS -- `<Link href="/evaluate-contract">` on line 47 |
| Each row links to `/contract/{id}` | PASS -- `href={/contract/${contract.id}}` on line 71 |
| Semantic tokens used consistently | PASS -- `text-muted`, `border-border`, `bg-surface`, `text-egregious-fg` all used correctly |
| XSS risk from contract names | PASS -- React's JSX escapes all interpolated strings by default. No `dangerouslySetInnerHTML`. |
| ScoreBadge reused from contract detail page | PASS -- imports from `@/app/contract/[id]/ScoreBadge` |

### FLAG: Zod schema vs backend `ContractListOut` mismatch

The backend `overall_fairness` field is `str | None` (any string). The frontend Zod schema uses `FairnessRatingSchema.nullable()` which restricts to `'fair' | 'non-standard' | 'dealbreaker'`. If the backend ever returns a value outside this enum, `safeParse` will fail and `setContracts([])` will show the empty state instead of an error -- silently hiding all contracts.

**Current mitigation:** `safeParse` with fallback to empty array (line 29). This is safe but could mask data issues.

**Recommendation:** Either (a) widen the Zod field to `z.string().nullable()` and validate display separately, or (b) accept the strict validation as a feature that catches backend drift. Current approach is acceptable but worth noting.

### FLAG: Loading state returns null

Line 34: `if (contracts === null) return null;` -- the page renders nothing during fetch. For a fast API this is fine, but a brief flash of empty content is possible. A skeleton loader would improve perceived performance but is not required for this milestone.

## Verdict

**PASS** -- Dashboard works correctly. Two minor flags noted (Zod strictness, null loading state), neither blocking.
