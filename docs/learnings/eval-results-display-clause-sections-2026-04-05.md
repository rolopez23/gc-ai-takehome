# Learnings: eval-results-display / clause-sections — 2026-04-05

## Pre-Human Run

**New loggable events:** 0

**Self-reflection notes (not loggable — caught in normal workflow):**
- Used `section_number` as React key without considering that multiple clauses can share a section number. Correctness reviewer caught it. When using domain fields as React keys, verify uniqueness within the rendered list — not just within the data model.

**Workflow compliance:** All steps followed in correct order. No wasted turns. 7 TDD cycles, all clean.

**Pattern check:** No new patterns triggered.
