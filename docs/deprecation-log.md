# Deprecation Log

## 2026-04-05 — Playbook-based ReviewResult model removed

**What**: The `ReviewResult` SQLAlchemy model and its Pydantic schemas (`ReviewResultOut`) were
designed around the 132-check playbook (`docs/gc-ai-takehome/gc_ai_playbook.md`). Fields included
`check_number`, `check_name`, `importance`, `status` (TRIGGERED/PASS/ABSENT/PARTIAL), `severity`,
`playbook_position`, `finding`, and `recommended_redline`.

**Why removed**: M3 keeps the clause-based fairness analysis model (fair/non-standard/dealbreaker)
that the LLM currently produces. The playbook check schema was dead code — never wired to the
frontend or called by any live path. YAGNI.

**Last commit with playbook models**: `b0c239a` (and earlier). The models lived in:
- `backend/models.py` — `ReviewResult` class
- `backend/schemas.py` — `ReviewResultOut`, `ContractReviewDetailOut.results`
- `backend/routers/reviews.py` — routes that loaded review results

**Playbook reference**: `docs/gc-ai-takehome/gc_ai_playbook.md` (132 checks across SaaS MSA,
Mutual NDA, Commercial MSA, DPA) — kept in docs for future reference.

**Resurrection path**: If we bring back per-check evaluation, start from commit `b0c239a` for the
schema shape, but expect to adapt field names to align with the clause-based model.
