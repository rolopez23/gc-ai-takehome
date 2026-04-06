# Review: add-failure-code-column

**Date**: 2026-04-05
**Commit**: 04cd1d5

## Simplify

The change is minimal and clean:
- No code reuse issues -- single column added to model, schema, and migration.
- No duplicated logic, no parameter sprawl, no unnecessary comments.
- `failure_code` is stringly-typed (free-form string rather than an enum), but this is intentional per the step plan -- the frontend maps codes to display labels, keeping the backend flexible.
- **Verdict**: Clean. No simplification needed.

## Review

### Findings

| # | Finding | Severity | Triage |
|---|---------|----------|--------|
| 1 | `ReviewOut.failure_code` has `= None` default but other nullable fields (e.g. `failure_message`, `summary`) do not set a default. This inconsistency means `failure_code` is optional during construction while the others are required. | Low | **Valid** -- harmless since `from_attributes=True` populates all fields from ORM, but worth noting for consistency. Could align in a future cleanup. |
| 2 | Migration uses `sa.String()` (unbounded VARCHAR). Model uses `mapped_column(nullable=True)` without specifying a type, which SQLAlchemy infers as `String`. These are consistent. | Info | **Dismissed** -- no issue. |
| 3 | No enum constraint on `failure_code` values at the DB level. Tests show values: `timeout`, `anthropic_error`, `too_large`, `parse_error`, `unknown`. | Low | **Speculative** -- a DB-level check constraint or Python enum would prevent typos, but adds coupling. Current approach is reasonable for an early-stage app. |
| 4 | Migration is fully reversible: `downgrade()` calls `op.drop_column`. | Info | N/A |
| 5 | Nullable column with no default is safe for existing rows -- they get NULL automatically. Schema default `None` matches. No type mismatch between model (`str | None`) and schema (`str | None`). | Info | N/A |

### Summary

No bugs, no edge-case gaps, no contract violations. The migration is reversible. The schema default handles existing rows correctly. The only valid (low-severity) observation is the inconsistent use of `= None` on `failure_code` vs. other nullable fields in `ReviewOut`.
