# Verify: polish-empty-and-error-states

**Date**: 2026-04-05
**Status**: PASS

## Checklist

| Criterion | Result |
|---|---|
| `EvaluationFailed` uses styled alert box with egregious tokens | PASS — line 103: `border-egregious-border bg-egregious-bg text-egregious-fg` with `role="alert"` |
| `EvaluationFailed` CTA is primary button (not underlined link) | PASS — line 107: `rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background` |
| `NoEvaluation` centered with `min-h-[60vh]` | PASS — line 42: `flex min-h-[60vh] flex-col items-center justify-center text-center` |
| `NoEvaluation` has diamond icon | PASS — line 43: `<span className="text-2xl text-muted">diamond</span>` |
| `NoEvaluation` CTA is primary button | PASS — line 46: `rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background` |
| `NotAContract` centered with `min-h-[60vh]` | PASS — line 88: same flex centering pattern |
| `NotAContract` has diamond icon | PASS — line 89 |
| `NotAContract` CTA is primary button | PASS — line 92 |

## Screenshot

Playwright screenshot of non-existent contract (`00000000-...`) confirms: vertically centered layout, muted diamond icon above title, descriptive text, and prominent dark CTA button.
