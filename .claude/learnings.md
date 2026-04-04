# Learnings Log

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Context
**What happened**: After completing auto tests for Step 1, skipped simplify/review/understand/human sign-off and jumped directly into Step 2 implementation. User had to intervene: "Can we respect the workflow?"
**Where it surfaced**: Human review
**Pattern tag**: `workflow-steps-skipped`

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Context
**What happened**: After human sign-off, attempted to move directly to Step 2 without running /learn-from-mistakes. User corrected: the order is sign-off → learn → next step.
**Where it surfaced**: Human review
**Pattern tag**: `workflow-steps-skipped`

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Context
**What happened**: Plan dashboard was not updated after completing auto tests. User had to point out the plan showed all ⬜ despite Step 1 being done.
**Where it surfaced**: Human review
**Pattern tag**: `plan-not-updated`

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Prompt
**What happened**: Used explicit `: boolean` return types on obvious validation functions. User preferred implicit types when the return is self-evident, and wanted a rule added to AGENTS.md.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `typescript-style-mismatch`

### 2026-04-04 · contract-upload-ui/file-drop-zone

**Category**: Human correction
**Error class**: Skill
**What happened**: Tests used `document.querySelector('input[type="file"]')` instead of RTL's `screen.getByLabelText`. Neither simplify nor review caught this anti-pattern.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `rtl-query-antipattern`

### 2026-04-04 · contract-upload-ui/file-drop-zone

**Category**: Human correction
**Error class**: Skill
**What happened**: Tests had unnecessary `as HTMLInputElement` type casts on RTL queries where the consuming API accepts `HTMLElement`. Simplify and review did not flag this.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `unnecessary-type-cast`

### 2026-04-04 · contract-upload-ui/file-drop-zone

**Category**: Human correction
**Error class**: Context
**What happened**: Test comments explained what the code already showed (e.g., "Use fireEvent to bypass the accept attribute filtering"). User flagged as noise — and noted that walkthrough questions matching comments aren't real comprehension tests.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `unnecessary-comments`

### 2026-04-04 · contract-upload-ui/upload-page

**Category**: Implementation hole
**Error class**: Specification
**What happened**: Spec and plan did not mention clearing form state after submit. User caught during sign-off that handleSubmit should reset file and instructions. Neither review nor simplify flagged this gap.
**Where it surfaced**: Human sign-off
**Pattern tag**: `missing-reset-after-action`

### 2026-04-04 · contract-upload-ui/upload-page

**Category**: Skill gap
**Error class**: Skill
**What happened**: After adding form reset, a mixed controlled/uncontrolled pattern was introduced in FileDropZone (both internal stagedFile state and external file prop). The first simplify pass did not run on this change — user had to explicitly request a re-run. The re-run correctly identified and fixed the dead state.
**Where it surfaced**: Human-requested simplify re-run
**Pattern tag**: `simplify-not-rerun-after-fix`
