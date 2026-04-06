# Step: polish-evaluate-page

> Part of: [plan.md](../plan.md) · Design: [design-spec.md](../design-spec.md)

## What This Step Delivers

Polishes the evaluate-contract page: display-tier title, consistent spacing, updated border colors on FileDropZone, styled error alert box using `getFailureMessage`, responsive button width.

## Done When

1. Title uses `text-2xl font-bold` (display tier)
2. Container uses `px-6 pt-12`
3. FileDropZone borders use `border-border` token
4. Error shows as styled alert box (not bare red text)
5. Evaluate button is full-width on mobile, auto on desktop
6. `getFailureMessage` used for poll-failure errors

## Cycles

### typography-and-spacing

**Test** — No automated tests (CSS changes).

**Code** — Update `evaluate-contract/page.tsx`:
- `text-3xl` → `text-2xl` on h1
- `px-4 py-12` → `px-6 pt-12` on container
- Button: add `w-full sm:w-auto`

Update `FileDropZone.tsx`:
- `border-foreground/20` → `border-border`
- Drag state: `border-blue-400 bg-blue-50/10` → `border-foreground/40 bg-foreground/[0.03]`
- Selected file border: `border-foreground/20` → `border-border`
- Remove button hover: `hover:bg-foreground/10` → `hover:bg-foreground/[0.05]`

**Refactor** — none

**Commit**: `design: polish evaluate page typography, spacing, and borders`

---

### error-alert-and-failure-message

**Test** — update existing `error-display.test.tsx`:
- **test_evaluate_page_shows_friendly_error_on_failure**: Mock poll returns `status: "failed"`, `failure_code: "timeout"`. Assert "The evaluation timed out" text visible.
- **test_evaluate_page_shows_generic_on_null_code**: Mock poll returns `failure_code: null`. Assert "Something went wrong" visible.

**Code** — Update `evaluate-contract/page.tsx`:
- Import `getFailureMessage`
- On failed poll result (line 72): `setError(getFailureMessage(result.failure_code))`
- Replace error `<p>` with styled alert:
  ```tsx
  <div className="flex gap-3 rounded-lg border border-egregious-border bg-egregious-bg p-4 text-sm text-egregious-fg" role="alert">
    <span>⚠</span>
    <p>{error}</p>
  </div>
  ```

**Refactor** — none

**Commit**: `design: styled error alert with friendly failure messages on evaluate page`

---

## Verification

Playwright screenshots:
1. Navigate to `/evaluate-contract` — confirm display-tier title, updated spacing
2. Trigger an error (upload with bad API key) — confirm styled alert box renders
3. Check FileDropZone borders look correct
4. Resize to mobile width — confirm button goes full-width
5. Dark mode — confirm alert box colors readable
