## Review: file-drop-zone (Step 2)
## Date: 2026-04-04

---

### Standard Review

#### Edge Cases
- **FileDropZone.tsx:45-48** — Cancelling the file picker after a validation error leaves the stale error visible. `handleInputChange` does nothing on cancel, so `setError(null)` never runs. · `Speculative: minor UX annoyance — error clears on next valid interaction. Not blocking.`
- **FileDropZone.tsx:72** — Replace requires remove-then-reselect, not a direct replace action. · `Dismissed: spec says "Replacing a file clears only the previous file selection" — the remove+re-upload flow satisfies this. Direct replace is a UX enhancement, not a spec gap.`
- **FileDropZone.tsx:61-63** — `handleDragLeave` fires on child elements, causing `isDragging` to flicker. · `Valid: well-known DnD issue. Fix with dragenter counter or relatedTarget check.`

---

### Edge Case Hunter

- **FileDropZone.tsx:68-69** — Empty dataTransfer.files on drop → guarded by `if (file)` · `Dismissed: handled`
- **FileDropZone.tsx:68** — Multi-file drop silently takes first file only · `Speculative: spec says single file; no user feedback needed per spec`
- **FileDropZone.tsx:26-43** — Error clears correctly when processFile called again · `Dismissed: handled`
- **FileDropZone.tsx:53** — handleRemove when inputRef.current is null → guarded by `if` · `Dismissed: handled`
- **FileDropZone.tsx:105** — Browse when inputRef is null → guarded by `?.` · `Dismissed: handled`
- **FileDropZone.tsx:29-33** — Validation fails while stagedFile is set → error set but hidden by early return · `Valid: if processFile is somehow called while staged, error would be invisible. In practice this can't happen since the drop zone is unmounted when staged, but it's a latent issue.`
- **FileDropZone.tsx:61-63** — dragLeave on child elements → flicker · `Valid: same as standard review finding`
- **FileDropZone.tsx:45-48** — Empty files on input cancel → guarded · `Dismissed: handled`

---

### Adversarial

1. **FileDropZone.tsx:68** — Multi-file drop, no feedback for discarded files · `Dismissed: spec is single-file; silent discard is acceptable`
2. **FileDropZone.tsx:72** — Replace requires two steps (remove then upload) · `Dismissed: satisfies spec as written`
3. **FileDropZone.tsx:61-63** — dragLeave child element flicker · `Valid: real UX bug`
4. **validation.ts** — Extension-only validation allows renamed malware · `Dismissed: spec decision, backend validates content`
5. **FileDropZone.tsx:26-43** — processFile doesn't call onFileChange(null) on validation failure · `Speculative: parent state isn't stale because onFileChange was never called with a file if validation fails. Only valid file selections trigger onFileChange.`
6. **FileDropZone.tsx:45-48** — Silent discard on picker cancel · `Dismissed: standard browser behavior`
7. **FileDropZone.tsx:111-117** — No aria-label on hidden input · `Speculative: input is triggered via button click, not direct keyboard nav. Could improve a11y but not a spec requirement.`
8. **FileDropZone.test.tsx:103** — `.closest('div')` selector is fragile · `Speculative: test works today; if DOM structure changes, test will catch it by failing`
9. **FileDropZone.test.tsx:18-23** — Accept attribute test hardcodes string order · `Dismissed: order matches ALLOWED_EXTENSIONS constant; if reordered, both change together`
10. **FileDropZone.tsx** — No test for isDragging visual state · `Speculative: visual state is cosmetic; behavioral tests cover the important paths`
11. **FileDropZone.tsx:14-18** — MiB vs MB labeling inconsistency · `Dismissed: standard industry practice to call 1024*1024 "MB" in file size contexts`
12. **FileDropZone.tsx:26** — setError(null) before re-setting causes brief flash · `Dismissed: React 18 batches these synchronously`

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 3 | 1 (stale error on cancel) | 2 | Useful — caught the dragLeave flicker clearly |
| Edge Case Hunter | 9 | 1 (validation fail while staged) | 4 | Useful — thorough path coverage, confirmed most handled |
| Adversarial | 12 | 4 (a11y, test fragility, no isDragging test, onFileChange on failure) | 5 | Useful — surfaced a11y gap worth noting |

**Notes:** One valid finding across all three: the `handleDragLeave` child-element flicker. Worth fixing — it's a known DnD pattern issue with a standard fix (drag counter).
