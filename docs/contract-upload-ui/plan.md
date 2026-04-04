# Plan: Contract Upload UI

> Spec: [docs/contract-upload-ui/spec.md](spec.md)

## Status Dashboard

| Step                                                  | Blocks              | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| ----------------------------------------------------- | ------------------- | --------------- | :--------: | :----: | :------: | :----: | :--------: | :---: |
| [file-validation](steps/file-validation.md)           | file-drop-zone, upload-page | `1b1947e` |     ✅     |   ➖   |    ✅    |   ✅   |     ✅     |  ✅   |
| [file-drop-zone](steps/file-drop-zone.md)             | upload-page         | `68af81a`       |     ✅     |   ➖   |    ✅    |   ✅   |     ✅     |  ✅   |
| [upload-page](steps/upload-page.md)                   | —                   | `bb89a6f`       |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow order per step:** Auto Tests → Verify → Simplify → Review → Understand → Human

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: E2E check — real curl or browser automation against a live system; ➖ if no external surface
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding.

---

## Branching Strategy

Single feature branch (`rl/frontend-upload`, already checked out). Steps are tightly sequential and small — commits per step, no need for per-step branches. Each step ends with a green commit.

---

## File Map

```
Create:  frontend/app/evaluate-contract/validation.ts       — Pure validation functions + constants
Create:  frontend/app/evaluate-contract/FileDropZone.tsx     — Drop zone component
Create:  frontend/app/evaluate-contract/page.tsx             — Page: assembles everything
Create:  frontend/__tests__/validation.test.ts               — Validation unit tests
Create:  frontend/__tests__/FileDropZone.test.tsx            — Drop zone component tests
Create:  frontend/__tests__/evaluate-contract-page.test.tsx  — Page integration tests
Modify:  frontend/package.json                               — Add vitest + testing-library deps
Create:  frontend/vitest.config.ts                           — Vitest config for Next.js/React
```

---

## Steps

### file-validation

Pure validation logic — no React, no DOM. Exports `ALLOWED_EXTENSIONS`, `MAX_FILE_SIZE_BYTES`, `validateFileExtension()`, and `validateFileSize()`. Also sets up Vitest + Testing Library as the test framework since none exists yet.

[→ Detailed plan](steps/file-validation.md)

### file-drop-zone

A `FileDropZone` component that handles drag-and-drop, file picker, extension/size validation with error display, staged file feedback (name + size + remove button), and file replacement. Uses the validation functions from step 1.

[→ Detailed plan](steps/file-drop-zone.md)

### upload-page

The `/evaluate-contract` page assembling the drop zone, a textarea for instructions, and an extracted `handleSubmit` that console.logs the `SubmitPayload`. File and textarea state are independent.

[→ Detailed plan](steps/upload-page.md)
