# Review: polish-empty-and-error-states

**Date**: 2026-04-05
**Verdict**: PASS — one simplification opportunity noted

## Simplify

- **Duplicated alert box markup**: The alert box in `EvaluationFailed` (page.tsx line 103) is nearly identical to the one in `evaluate-contract/page.tsx` (line 113). Both use `flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg` with a warning icon and message. The step plan called for extracting a shared `ErrorAlert` component if >5 lines duplicated. The markup is 4 lines (div, span, p, closing div), so it falls just under the threshold. Extraction is optional but would reduce future drift.
- **Primary CTA button style is consistent**: All three dead-end states (`NoEvaluation`, `NotAContract`, `EvaluationFailed`) use the same `rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background` pattern. The `EvaluationFailed` version adds `inline-block` since it's inside a block-flow container rather than a flex-center — this is correct.

## Correctness

| Check | Result |
|---|---|
| `NoEvaluation` uses `min-h-[60vh]` | PASS — line 42 |
| `NotAContract` uses `min-h-[60vh]` | PASS — line 88 |
| `EvaluationFailed` does NOT use `min-h-[60vh]` | Correct — it uses `PAGE_CONTAINER` instead, since it has a title + alert (not a centered dead-end) |
| Primary CTA button style consistent across all three | PASS — same token set with minor `inline-block` variation |
| Alert box has `role="alert"` | PASS — line 103 |

## Observations

1. **`EvaluationFailed` layout differs from centered states**: It uses `PAGE_CONTAINER` (top-aligned) while the other two use centered flex. This is intentional — it has a title bar and alert, not a single-message dead end.
2. **No `ErrorAlert` component extracted**: Per the step plan's threshold (>5 lines), extraction was not required. If a third alert box appears in the codebase, extraction should be revisited.

## Risks

None. All changes are CSS/layout only with no logic changes.
