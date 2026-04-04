# Step: file-validation

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Pure validation functions for contract file uploads — extension checking and size checking — plus the constants they depend on. No React, no DOM. Also bootstraps Vitest + Testing Library since the project has no test framework yet.

## Done When

`npx vitest run` passes all validation tests. `validateFileExtension` and `validateFileSize` are exported and tested for happy path, rejection, and edge cases.

## Cycles

### test-framework-setup

**Test** — create a trivial test file and run `npx vitest run`. It should fail because vitest is not installed:

```typescript
// frontend/__tests__/validation.test.ts
import { describe, it, expect } from 'vitest';

describe('validation smoke test', () => {
  it('runs', () => {
    expect(true).toBe(true);
  });
});
```

**Code** — install deps and create config:

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @vitejs/plugin-react jsdom
```

```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
  },
  resolve: {
    alias: { '@': '.' },
  },
});
```

Confirm the smoke test passes.

**Refactor** — remove the smoke test once real tests exist (next cycle).

**Commit**: `Add vitest + testing-library test framework`

---

### validate-file-extension

**Test** — write these tests and confirm they fail (module doesn't exist yet):

```typescript
// frontend/__tests__/validation.test.ts
import { describe, it, expect } from 'vitest';
import { validateFileExtension, ALLOWED_EXTENSIONS } from '@/app/evaluate-contract/validation';

describe('validateFileExtension', () => {
  it('accepts .pdf files', () => {
    expect(validateFileExtension('contract.pdf')).toBe(true);
  });

  it('accepts .txt files', () => {
    expect(validateFileExtension('contract.txt')).toBe(true);
  });

  it('accepts .doc files', () => {
    expect(validateFileExtension('contract.doc')).toBe(true);
  });

  it('accepts .docx files', () => {
    expect(validateFileExtension('contract.docx')).toBe(true);
  });

  it('rejects .png files', () => {
    expect(validateFileExtension('image.png')).toBe(false);
  });

  it('rejects files with no extension', () => {
    expect(validateFileExtension('README')).toBe(false);
  });

  it('is case-insensitive', () => {
    expect(validateFileExtension('CONTRACT.PDF')).toBe(true);
  });

  it('checks the last extension only', () => {
    expect(validateFileExtension('file.tar.pdf')).toBe(true);
    expect(validateFileExtension('file.pdf.exe')).toBe(false);
  });
});

describe('ALLOWED_EXTENSIONS', () => {
  it('contains exactly .pdf, .txt, .doc, .docx', () => {
    expect([...ALLOWED_EXTENSIONS]).toEqual(['.pdf', '.txt', '.doc', '.docx']);
  });
});
```

**Code** — create `frontend/app/evaluate-contract/validation.ts`:

```typescript
export const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx'] as const;

export function validateFileExtension(fileName: string): boolean {
  const ext = fileName.slice(fileName.lastIndexOf('.')).toLowerCase();
  return ALLOWED_EXTENSIONS.includes(ext as typeof ALLOWED_EXTENSIONS[number]);
}
```

**Refactor** — none.

**Commit**: `Add file extension validation with tests`

---

### validate-file-size

**Test** — add to the same test file:

```typescript
import { validateFileSize, MAX_FILE_SIZE_BYTES } from '@/app/evaluate-contract/validation';

describe('validateFileSize', () => {
  it('accepts files under 5 MB', () => {
    expect(validateFileSize(1024)).toBe(true);
  });

  it('accepts files exactly at 5 MB', () => {
    expect(validateFileSize(5 * 1024 * 1024)).toBe(true);
  });

  it('rejects files over 5 MB', () => {
    expect(validateFileSize(5 * 1024 * 1024 + 1)).toBe(false);
  });

  it('accepts zero-byte files', () => {
    expect(validateFileSize(0)).toBe(true);
  });
});

describe('MAX_FILE_SIZE_BYTES', () => {
  it('is 5 MB', () => {
    expect(MAX_FILE_SIZE_BYTES).toBe(5 * 1024 * 1024);
  });
});
```

**Code** — add to `validation.ts`:

```typescript
export const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

export function validateFileSize(sizeInBytes: number): boolean {
  return sizeInBytes <= MAX_FILE_SIZE_BYTES;
}
```

**Refactor** — none.

**Commit**: `Add file size validation with tests`

---

## LLM Verification

**N/A** — pure functions with no external surface. Vitest tests are the verification.
