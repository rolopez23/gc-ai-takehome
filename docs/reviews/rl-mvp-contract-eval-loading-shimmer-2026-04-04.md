## Review: loading-shimmer
## Date: 2026-04-04

---

### Standard Review

#### Bugs
- **page.tsx:71-73** — `finally` block resets file and instructions unconditionally. On error, user loses input and must re-upload. Reset should only happen on success. · `[Valid — move reset to success path]`
- **page.tsx:69** — `evaluateContract` throws on `!res.ok` but `handleSubmit` has no catch block. Unhandled promise rejection. · `[Valid — add minimal catch, error-display step will expand it]`

---

### Edge Case Hunter

Empty array — all loading-state paths are handled within scope.

---

### Adversarial

1. **No file size guard before file.text()** · `[Dismissed — FileDropZone already validates 5MB max]`
2. **Errors silently swallowed, no catch** · `[Valid — same as standard review]`
3. **State reset in finally regardless of outcome** · `[Valid — same as standard review]`
4. **evaluateContract untestable without global fetch mock** · `[Dismissed — standard pattern for Next.js client components; tests already mock fetch]`
5. **No AbortController on unmount** · `[Dismissed — cancel-on-unmount is a separate step in the plan]`
6. **aria-busy on container not live region** · `[Speculative — aria-busy on the updating container is the correct pattern per WAI-ARIA]`
7. **role="status" conditionally rendered** · `[Valid — live region should be persistently mounted with dynamic text]`
8. **textarea has no label** · `[Valid — added to TODO.md accessibility section]`
9. **No form element, no Enter-key submission** · `[Speculative — deliberate for MVP; noted in TODO]`
10. **evaluateContract return value discarded** · `[Dismissed — success-navigation step will wire this up]`
11. **Empty file passes guards** · `[Dismissed — API route validates non-empty text]`
12. **Hardcoded 3 clause cards in shimmer** · `[Dismissed — skeleton is approximate by design]`
13. **HEIGHT/WIDTH maps could fail silently** · `[Dismissed — TypeScript enforces keyof, missing keys are compile errors]`

---

## Summary

**3 valid findings to fix now:**

1. Move state reset from `finally` to success path only
2. Add minimal catch block to prevent unhandled rejection
3. Persist `role="status"` live region in DOM, toggle text

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 2 | 0 | 2 | Useful — caught the two real bugs cleanly |
| Edge Case Hunter | 0 | 0 | 0 | Correct — no unhandled loading paths |
| Adversarial | 13 | 1 (live region mounting) | 2 | Useful — found the ARIA live region issue others missed |
