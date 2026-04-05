# Improvement Roadmap

Items to address after MVP ships. Not blockers — quality and polish work.

## Learning

- [ ] **Pydantic `from_attributes`** — How Pydantic reads from ORM objects vs dicts. Docs: https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.from_attributes
- [ ] **Schema drift safeguard** — Add a CI test or review check that verifies SQLAlchemy model types, Pydantic schema types, and frontend Zod types stay aligned (e.g. a test that generates JSON schema from Pydantic and compares to Zod's expected shape)

## M3 Walkthrough Follow-ups (Python learning)

- [ ] **`deferred` loading** — What changes at the SQL level when a column is deferred vs not?
- [ ] **`from_attributes`** — If you had a plain dict instead of an ORM object, would `from_attributes=True` help or hurt?
- [ ] **prompt.py Pydantic models** — These don't store data. What two things do they produce that other parts consume?
- [ ] **`selectinload`** — What error would you get if you removed it and tried to return `review.clauses` from an async endpoint?
- [ ] **conftest session patching** — Upload endpoint and background task each open their own DB session. Why does that matter for testing?

## Post-M3

- [ ] **Update README** — Document LibreOffice as a prerequisite, `make reset-db` command, new env vars (`ANTHROPIC_API_KEY`, `CORS_ORIGIN_REGEX`)
- [ ] **Harden CORS for production** — Replace regex with explicit `allow_origins` for prod deployments
- [ ] **Blob storage abstraction** — Move from PostgreSQL blob storage to AWS S3 / GCS for production; keep PSQL for dev
- [ ] **Contract list/history page** — Fast follow from M3
- [ ] **Background task durability** — Migrate from FastAPI BackgroundTasks to Celery/ARQ if reliability becomes an issue

## Accessibility / ARIA

- [ ] Audit FileDropZone for screen reader support (drag-and-drop alternatives, file state announcements)
- [ ] Add `aria-label` to textarea (currently relies on placeholder only)
- [ ] Add error announcement via `aria-live` for inline error display (error-display step)
- [ ] Audit results page (`/contract/[uuid]`) for heading hierarchy and landmark regions
- [ ] Test full flow with VoiceOver / screen reader

## Eval Pipeline

- [ ] Re-run full contract suite on Haiku 4.5 with `max_tokens: 8192` after fence stripping
- [ ] Investigate contract_3_nonstandard and contract_4_minor_issues scoring accuracy
- [ ] Add TTFT measurement to verification script
- [ ] Build automated eval runner (run all contracts, compare against benchmarks, report diffs)

## Prompt / Model

- [ ] LLM summary text can contradict its own clause breakdown (e.g. "4 fair clauses" but only 2 tagged fair). Add a post-processing validation step or tighten the prompt to derive summary counts from the actual clauses array.

## API Hardening

- [ ] Wire `instructions` through api-route to the prompt (currently sent but ignored server-side)
- [ ] Add request size limit on `/api/evaluate`
- [ ] Add structured logging to api-route catch block
- [ ] Add health-check endpoint that validates `ANTHROPIC_API_KEY` at startup

## Frontend Polish

- [ ] Loading shimmer stagger animation (CSS animation-delay on clause cards)
- [ ] Transition between form and shimmer states (fade/slide)
- [ ] Better error UX than just resetting the form silently on failure
