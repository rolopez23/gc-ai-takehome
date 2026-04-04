# Step: file-drop-zone

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

A `FileDropZone` React component that lets a user stage a single contract file via drag-and-drop or file picker. Shows validation errors for wrong extension or oversized files. Displays staged file feedback (name, formatted size, remove button). Calls an `onFileChange` callback when file state changes.

## Done When

All component tests pass. The drop zone renders, accepts valid files, rejects invalid ones with error messages, shows staged file info, and supports remove/replace.

## Cycles

### render-empty-state

**Test** — write and confirm it fails (component doesn't exist):

```tsx
// frontend/__tests__/FileDropZone.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FileDropZone } from '@/app/evaluate-contract/FileDropZone';

describe('FileDropZone', () => {
  it('renders the drop zone with browse prompt', () => {
    render(<FileDropZone onFileChange={vi.fn()} />);
    expect(screen.getByText(/drag.+drop/i)).toBeInTheDocument();
    expect(screen.getByText(/browse/i)).toBeInTheDocument();
  });

  it('has a hidden file input with correct accept types', () => {
    render(<FileDropZone onFileChange={vi.fn()} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.accept).toBe('.pdf,.txt,.doc,.docx');
  });
});
```

**Code** — create `frontend/app/evaluate-contract/FileDropZone.tsx` with a minimal `'use client'` component: a div with drop zone text, a hidden file input with the accept attribute, and a "Browse" button that triggers the input. Accept an `onFileChange: (file: File | null) => void` prop.

**Refactor** — none.

**Commit**: `Add FileDropZone empty state rendering`

---

### file-picker-selection

**Test** — add tests for selecting a valid file via the file input:

```tsx
import userEvent from '@testing-library/user-event';

it('stages a valid file and calls onFileChange', async () => {
  const onFileChange = vi.fn();
  render(<FileDropZone onFileChange={onFileChange} />);

  const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);

  expect(onFileChange).toHaveBeenCalledWith(file);
  expect(screen.getByText('contract.pdf')).toBeInTheDocument();
});
```

**Code** — add `onChange` handler to the file input that validates extension + size, stages the file in local state, and calls `onFileChange`. Show file name and formatted size when staged.

**Refactor** — extract a `formatFileSize` helper if needed (e.g., "1.2 MB", "450 KB").

**Commit**: `Add file picker selection and staged file display`

---

### validation-errors

**Test** — test rejection for invalid extension and oversized files:

```tsx
it('shows error for invalid file extension', async () => {
  const onFileChange = vi.fn();
  render(<FileDropZone onFileChange={onFileChange} />);

  const file = new File(['content'], 'image.png', { type: 'image/png' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);

  expect(screen.getByText(/file type not allowed/i)).toBeInTheDocument();
  expect(onFileChange).not.toHaveBeenCalled();
});

it('shows error for oversized file', async () => {
  const onFileChange = vi.fn();
  render(<FileDropZone onFileChange={onFileChange} />);

  const bigContent = new ArrayBuffer(6 * 1024 * 1024);
  const file = new File([bigContent], 'big.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);

  expect(screen.getByText(/5 MB/i)).toBeInTheDocument();
  expect(onFileChange).not.toHaveBeenCalled();
});
```

**Code** — add validation checks before staging. If validation fails, set an error string in state and render it. Do not stage the file or call `onFileChange`.

**Refactor** — none.

**Commit**: `Add validation error display for invalid files`

---

### remove-and-replace

**Test** — test remove button clears file, and selecting a new file replaces the old one:

```tsx
it('removes staged file when remove button is clicked', async () => {
  const onFileChange = vi.fn();
  render(<FileDropZone onFileChange={onFileChange} />);

  const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(input, file);
  expect(screen.getByText('contract.pdf')).toBeInTheDocument();

  await userEvent.click(screen.getByRole('button', { name: /remove/i }));
  expect(screen.queryByText('contract.pdf')).not.toBeInTheDocument();
  expect(onFileChange).toHaveBeenLastCalledWith(null);
});

it('replaces staged file when a new file is selected', async () => {
  const onFileChange = vi.fn();
  render(<FileDropZone onFileChange={onFileChange} />);

  const file1 = new File(['a'], 'first.pdf', { type: 'application/pdf' });
  const file2 = new File(['b'], 'second.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;

  await userEvent.upload(input, file1);
  expect(screen.getByText('first.pdf')).toBeInTheDocument();

  await userEvent.upload(input, file2);
  expect(screen.queryByText('first.pdf')).not.toBeInTheDocument();
  expect(screen.getByText('second.docx')).toBeInTheDocument();
});
```

**Code** — add a remove button to the staged file display that clears state and calls `onFileChange(null)`. Ensure re-selecting a file replaces the current one.

**Refactor** — none.

**Commit**: `Add file remove and replace behavior`

---

### drag-and-drop

**Test** — test drag-and-drop interactions:

```tsx
import { fireEvent } from '@testing-library/react';

it('accepts a valid file via drag and drop', () => {
  const onFileChange = vi.fn();
  render(<FileDropZone onFileChange={onFileChange} />);

  const dropZone = screen.getByText(/drag.+drop/i).closest('div')!;
  const file = new File(['content'], 'contract.txt', { type: 'text/plain' });

  fireEvent.dragOver(dropZone, { dataTransfer: { files: [file] } });
  fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

  expect(onFileChange).toHaveBeenCalledWith(file);
  expect(screen.getByText('contract.txt')).toBeInTheDocument();
});

it('shows visual feedback during drag over', () => {
  render(<FileDropZone onFileChange={vi.fn()} />);

  const dropZone = screen.getByText(/drag.+drop/i).closest('div')!;
  fireEvent.dragEnter(dropZone, { dataTransfer: { files: [] } });

  // Drop zone should have a visual indicator (e.g., border color change)
  expect(dropZone).toHaveClass(/drag|active|highlight/i);
});
```

**Code** — add `onDragOver`, `onDragEnter`, `onDragLeave`, `onDrop` handlers to the drop zone div. On drop, extract the first file from `dataTransfer.files`, run the same validation as the file picker, and stage or error. Add a `isDragging` state for visual feedback.

**Refactor** — extract shared validation + staging logic used by both the file input handler and the drop handler into a single `processFile(file: File)` internal function.

**Commit**: `Add drag-and-drop support with visual feedback`

---

## LLM Verification

**N/A** — component tests cover behavior. Visual verification happens in the upload-page step when the full page is rendered in a browser.
