# Step: upload-page

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

The `/evaluate-contract` page that assembles the `FileDropZone`, an instructions textarea, and an extracted submit handler. Navigating to the route renders the full upload UI. Clicking submit logs the `SubmitPayload` to the console. File and textarea state are independent.

## Done When

All page tests pass. The dev server renders the page at `/evaluate-contract`. Submit logs the correct payload. Removing a file does not clear the textarea.

## Cycles

### page-renders

**Test** — write and confirm it fails (page doesn't exist as a composed component yet):

```tsx
// frontend/__tests__/evaluate-contract-page.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import EvaluateContractPage from '@/app/evaluate-contract/page';

describe('EvaluateContractPage', () => {
  it('renders the page heading', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByRole('heading', { name: /evaluate/i })).toBeInTheDocument();
  });

  it('renders the file drop zone', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
  });

  it('renders the instructions textarea', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByPlaceholderText(/instruction/i)).toBeInTheDocument();
  });

  it('renders the submit button', () => {
    render(<EvaluateContractPage />);
    expect(screen.getByRole('button', { name: /evaluate/i })).toBeInTheDocument();
  });
});
```

**Code** — create `frontend/app/evaluate-contract/page.tsx` as a `'use client'` component:
- State: `file: File | null`, `instructions: string`
- Renders: heading, `FileDropZone` with `onFileChange`, textarea with `onChange`, submit button
- Submit button disabled when no file is staged

**Refactor** — none.

**Commit**: `Add evaluate-contract page with layout`

---

### submit-handler

**Test** — test that clicking submit logs the correct payload:

```tsx
import userEvent from '@testing-library/user-event';

it('logs SubmitPayload to console on submit', async () => {
  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
  render(<EvaluateContractPage />);

  // Stage a file
  const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);

  // Type instructions
  await userEvent.type(screen.getByPlaceholderText(/instruction/i), 'Focus on IP clauses');

  // Submit
  await userEvent.click(screen.getByRole('button', { name: /evaluate/i }));

  expect(consoleSpy).toHaveBeenCalledWith(
    expect.objectContaining({
      fileName: 'contract.pdf',
      fileType: '.pdf',
      instructions: 'Focus on IP clauses',
    })
  );
  consoleSpy.mockRestore();
});

it('disables submit button when no file is staged', () => {
  render(<EvaluateContractPage />);
  expect(screen.getByRole('button', { name: /evaluate/i })).toBeDisabled();
});
```

**Code** — implement the extracted `handleSubmit` function:

```typescript
function handleSubmit(payload: SubmitPayload): void {
  console.log(payload);
}
```

Wire the button's `onClick` to build the `SubmitPayload` from state and call `handleSubmit`. Disable the button when `file` is null.

**Refactor** — none.

**Commit**: `Add extracted submit handler with console.log`

---

### independent-state

**Test** — confirm file and textarea state are independent:

```tsx
it('does not clear instructions when file is removed', async () => {
  render(<EvaluateContractPage />);

  // Type instructions first
  await userEvent.type(screen.getByPlaceholderText(/instruction/i), 'Check indemnification');

  // Stage then remove a file
  const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);
  await userEvent.click(screen.getByRole('button', { name: /remove/i }));

  // Instructions should persist
  expect(screen.getByPlaceholderText(/instruction/i)).toHaveValue('Check indemnification');
});

it('does not clear file when instructions are cleared', async () => {
  render(<EvaluateContractPage />);

  // Stage a file
  const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);

  // Type then clear instructions
  const textarea = screen.getByPlaceholderText(/instruction/i);
  await userEvent.type(textarea, 'Some text');
  await userEvent.clear(textarea);

  // File should still be staged
  expect(screen.getByText('contract.pdf')).toBeInTheDocument();
});
```

**Code** — this should already work if file and instructions are separate `useState` calls. If any coupling exists, fix it.

**Refactor** — final pass: clean up any rough edges in the page layout and component composition.

**Commit**: `Verify independent file and instruction state`

---

## LLM Verification

Start the dev server and verify in a browser:

```bash
cd frontend && npm run dev
# Navigate to http://localhost:<port>/evaluate-contract
```

**Check:**
1. Page renders with heading, drop zone, textarea, and disabled submit button
2. Drag a `.pdf` onto the drop zone → file name and size appear, submit enables
3. Click remove → returns to empty state, submit disables
4. Select a `.png` via browse → error message appears, file not staged
5. Select a 6 MB `.pdf` → size error appears
6. Stage a file, type instructions, click submit → open browser console, verify `SubmitPayload` logged
7. Remove file → instructions textarea still has text
