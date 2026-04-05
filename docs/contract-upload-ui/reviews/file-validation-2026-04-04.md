## Review: file-validation (Step 1)
## Date: 2026-04-04

---

### Standard Review

#### Edge Cases
- **validation.ts:4-8** — A dotfile like `.pdf` (no base name) passes validation since `dotIndex === 0` and `ext === ".pdf"` is in the allowed list. · `Dismissed: browser File objects always have real filenames; dotfiles without base names won't appear in file upload contexts`
- **validation.ts:11-13** — Negative `sizeInBytes` (e.g., `-1`) passes validation. · `Dismissed: browser File.size is always non-negative; this is client-side only`

#### Contract Violations
- **validation.ts** — Extension-only validation means renamed files bypass the check. · `Dismissed: spec explicitly accepts this trade-off; backend does deeper validation`

---

### Edge Case Hunter

- **validation.ts:4-8** — Empty string input, `dotIndex === -1` branch returns false correctly · `Dismissed: handled correctly`
- **validation.ts:4-8** — fileName ends with dot (e.g., `file.`), ext becomes `.` which is rejected · `Dismissed: handled correctly`
- **validation.ts:4-8** — Dotfile `.pdf` with no base name passes validation · `Dismissed: same as standard review finding — browser File objects have real names`
- **validation.ts:4-8** — fileName contains path separators (e.g., `../evil.pdf`) · `Dismissed: browser File.name never includes path separators`
- **validation.ts:11-13** — Negative sizeInBytes · `Dismissed: browser File.size is non-negative`
- **validation.ts:11-13** — NaN or Infinity sizeInBytes · `Dismissed: browser File.size is always a finite integer`
- **validation.ts:11-13** — Zero-byte file passes · `Dismissed: spec explicitly allows zero-byte files (test confirms this behavior)`

---

### Adversarial

1. **validation.ts:1** — Rename bypass (malware.exe → malware.pdf) · `Dismissed: spec decision — backend does deeper validation`
2. **validation.ts:4** — Dotfile/hidden file prefix edge case · `Dismissed: browser File.name doesn't include path prefixes`
3. **validation.ts:1** — No distinction between "no extension" and "wrong extension" for error messaging · `Speculative: valid UX concern but the component layer handles this by showing a single "file type not allowed" message which covers both cases adequately`
4. **validation.ts:1** — Zero-byte file accepted · `Dismissed: spec allows it; test confirms`
5. **validation.ts:8** — `as const` + cast is fragile if array type changes · `Dismissed: premature concern; array is 4 items and not expected to change shape`
6. **validation.ts:1** — No guard against null/undefined fileName · `Dismissed: TypeScript enforces string type; callers are typed`
7. **validation.ts:11** — Negative sizeInBytes · `Dismissed: browser API guarantee`
8. **validation.ts** — No combined `validateFile` entry point with structured error · `Speculative: valid design consideration for future, but current scope is intentionally minimal — component does the assembly`
9. **validation.test.ts** — Double extension `contract.exe.pdf` passes (phishing vector) · `Dismissed: this is correct behavior per spec — we validate by last extension only. Backend can flag double extensions if needed`
10. **validation.test.ts** — Case-insensitivity test coverage uncertain · `Dismissed: the test exists and passes; implementation lowercases extension`
11. **vitest.config.ts:1** — `globals: true` exposes test globals project-wide · `Speculative: minor concern; vitest globals are scoped to test files by convention, and tsconfig doesn't reference vitest types in non-test code`
12. **validation.ts** — No shared schema between frontend and backend for allowed extensions/size · `Speculative: valid concern for M1 backend integration — worth noting but out of scope for this step`

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 3 | 0 | 3 | Redundant — findings were all also caught by others |
| Edge Case Hunter | 7 | 1 | 6 | Useful — exhaustive path trace confirmed all paths handled |
| Adversarial | 12 | 4 | 8 | Useful — surfaced speculative concerns (combined validator, shared schema) worth noting for later |

**Notes:** All findings dismissed or speculative for this scope. The code is simple, correct, and well-tested for its intended purpose (client-side pre-validation). Speculative items #8 (combined validator) and #12 (shared schema) are worth revisiting during backend integration but are not actionable now.
