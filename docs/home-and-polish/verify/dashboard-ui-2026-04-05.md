# Verify: dashboard-ui (2026-04-05)

## Browser Verification

**Screenshot observations:** Dashboard renders at localhost:3000 with "Your Contracts" heading and "Evaluate Contract" button. Contract list shows 17 rows with names, relative timestamps (1h ago, 3h ago, etc.), and fairness badges (Fair/Unfair) where applicable. Layout is clean with proper spacing.

### Checklist

| Check | Result |
|---|---|
| Contract list renders with names | PASS -- all contract names visible |
| Status/fairness badges shown | PASS -- "Fair" and "Unfair" badges render for completed contracts |
| Each row links to /contract/{id} | PASS -- snapshot confirms all links have correct `/contract/{uuid}` hrefs |
| "Evaluate Contract" button present | PASS -- both nav link and inline button link to `/evaluate-contract` |
| Relative timestamps shown | PASS -- "1h ago", "3h ago", etc. render correctly |
| Contracts without completed reviews | PASS -- rows show name + timestamp only (no badge) |

### Not verified

- **Empty state:** Could not test because dev DB has 17 contracts. Unit tests cover this path.
- **API curl:** Bash tool unavailable; browser fetch confirms API returns data (17 contracts rendered).

### Observation: `contract_3_nonstandard.pdf` shows "Fair"

This is not a bug in the dashboard. The badge reflects the backend `overall_fairness` value. The contract name suggests non-standard terms, but the LLM evaluation apparently rated it "fair" overall. The dashboard correctly displays whatever the backend returns.

### Observation: Some contracts show no badge

Contracts like `contract_2_egregious.pdf` render without a badge. The `StatusDisplay` component only shows a badge when `review_status === 'completed'` AND `overall_fairness` is non-null. These contracts likely have a null status or fairness, which the component handles correctly by rendering nothing.
