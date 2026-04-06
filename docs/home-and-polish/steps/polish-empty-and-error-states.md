# Step: polish-empty-and-error-states

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Styles the failed, not-found, and not-a-contract states on the detail page with centered layouts, styled alert boxes, and prominent CTAs. These are the "dead end" screens — they should guide the user back to action.

## Done When

1. `EvaluationFailed` uses styled alert box (matching evaluate page error banner)
2. `NoEvaluation` and `NotAContract` are vertically centered with muted icon + CTA button
3. CTAs use primary button style (not underlined links)

## Cycles

### centered-dead-end-states

**Test** — No automated tests (visual layout).

**Code** — Update `contract/[id]/page.tsx`:

`EvaluationFailed`:
- Wrap error message in styled alert box:
  ```tsx
  <div className="flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg">
    <span>⚠</span>
    <p>{message}</p>
  </div>
  ```
- Change back link to primary button: `rounded-lg bg-foreground px-6 py-3 text-sm font-medium text-background`

`NoEvaluation` and `NotAContract`:
- Container: `flex min-h-[60vh] flex-col items-center justify-center text-center`
- Add muted diamond icon: `<span className="text-2xl text-muted">◆</span>`
- Title: `text-2xl font-bold mt-4`
- Description: `text-sm text-muted mt-2 max-w-sm`
- CTA: primary button style linking to `/evaluate-contract`

**Refactor** — If the alert box JSX is identical to the evaluate page one, extract a shared `ErrorAlert` component. Only if >5 lines duplicated.

**Commit**: `design: style dead-end states with centered layouts and prominent CTAs`

---

## Verification

Playwright screenshots:
1. Navigate to a failed contract — confirm styled alert box + primary CTA button
2. Navigate to a non-existent contract ID — confirm centered not-found state with icon
3. Navigate to a "not a contract" result — confirm centered state with explanation
4. Dark mode — confirm all states readable
5. Visually evaluate: do these dead-end screens feel intentional and guide the user forward?
