## Review: clause-sections step
## Date: 2026-04-05

---

### Simplify

Code is clean. Minor note: `groupByFairness` could be memoized, but the clause list is small and grouping is O(n) — not worth adding complexity.

---

### Correctness Review

#### Bugs
- **ClauseSection.tsx:46** — `section_number` used as React key is not unique across clauses (multiple clauses can share a section). Causes reconciliation bugs. · `[Valid — fixed: changed to compound key with index]`

#### Everything Else
Clean. Section order, counts, collapsed state, empty placeholders, scroll constraint all correct per spec.

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Simplify | 0 | 0 | 0 | Useful — correctly clean |
| Correctness | 1 valid | 1 | 0 | Useful — caught real React key bug |

**Notes:** Good catch on the non-unique key. This is a common React anti-pattern when using domain identifiers that aren't truly unique per list item.
