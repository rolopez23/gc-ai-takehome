# Plan: Agentic Contract Evaluation Pipeline

> Spec: [docs/agentic-eval-pipeline/spec.md](spec.md)

## Framework Decision

**Custom orchestrator on the Anthropic SDK** — no LangChain, no LangGraph.

The pipeline is linear with one fan-out/fan-in step (parallel clause evaluation). The Anthropic
SDK already provides tool use, async client, and retry. A custom orchestrator gives precise
control over NDJSON event emission, per-agent model config, and token tracking — all of which
framework abstractions would fight against. The total orchestration code is ~200 lines.

## File Map

```
Create:  backend/services/playbook.py                          — Playbook markdown parser + get_playbook lookup
Create:  backend/services/agents/__init__.py                   — Agent package
Create:  backend/services/agents/base.py                       — Base agent runner (tool loop, retry, model config, token tracking)
Create:  backend/services/agents/verifier.py                   — Contract verifier agent (prompt + tool def)
Create:  backend/services/agents/splitter.py                   — Clause splitter agent (prompt + tool def + enum constraint)
Create:  backend/services/agents/evaluator.py                  — Clause evaluator agent (prompt + tool def)
Create:  backend/services/agents/headline.py                   — Headline generator agent (prompt + tool def)
Create:  backend/services/synthesis.py                         — Deterministic synthesis function (overall_fairness, assembly)
Create:  backend/services/orchestrator.py                      — Pipeline orchestrator (verify → split → persist → eval → headline → synth)
Create:  backend/services/streaming.py                         — NDJSON event emitter (EventEmitter class)
Create:  backend/migrations/versions/002_agentic_pipeline.py   — Alembic migration for new columns
Modify:  backend/models.py                                     — Add columns to ContractReview + ReviewClause
Modify:  backend/schemas.py                                    — Add streaming schemas (or keep separate)
Modify:  backend/routers/reviews.py                            — Add GET /api/reviews/{id}/stream
Modify:  backend/main.py                                       — Playbook startup validation
Create:  backend/tests/test_playbook.py                        — Playbook parser + lookup tests
Create:  backend/tests/test_agent_base.py                      — Base agent runner tests
Create:  backend/tests/test_verifier.py                        — Verifier agent tests
Create:  backend/tests/test_splitter.py                        — Splitter agent tests
Create:  backend/tests/test_evaluator.py                       — Evaluator agent tests
Create:  backend/tests/test_headline.py                        — Headline agent tests
Create:  backend/tests/test_synthesis.py                       — Synthesis function tests
Create:  backend/tests/test_orchestrator.py                    — Pipeline orchestration tests
Create:  backend/tests/test_stream_endpoint.py                 — NDJSON streaming endpoint tests
Create:  frontend/app/evaluate-contract/stream.ts              — NDJSON stream reader utility
Modify:  frontend/app/evaluate-contract/types.ts               — New Zod schemas for streaming events
Modify:  frontend/app/evaluate-contract/page.tsx               — Stream consumer (minimum viable)
Modify:  frontend/app/contract/[id]/page.tsx                   — Severity-tier bucket rendering
Create:  frontend/__tests__/stream.test.ts                     — Stream reader tests
Create:  frontend/__tests__/streaming-types.test.ts            — Streaming Zod schema tests
```

## Status Dashboard

| Step                                                                  | Blocks                                      | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| --------------------------------------------------------------------- | ------------------------------------------- | --------------- | :--------: | :----: | :------: | :----: | :--------: | :---: |
| [playbook-parser](steps/playbook-parser.md)                           | clause-splitter, clause-evaluator            | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ⬜   |
| [schema-migration](steps/schema-migration.md)                         | pipeline-orchestration                       | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ⬜   |
| [agent-core](steps/agent-core.md)                                     | contract-verifier, clause-splitter, clause-evaluator, headline-synthesis | — | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ |
| [contract-verifier](steps/contract-verifier.md)                       | pipeline-orchestration                       | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ⬜     |  ⬜   |
| [clause-splitter](steps/clause-splitter.md)                           | pipeline-orchestration                       | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ⬜     |  ⬜   |
| [clause-evaluator](steps/clause-evaluator.md)                         | pipeline-orchestration                       | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ⬜     |  ⬜   |
| [headline-synthesis](steps/headline-synthesis.md)                     | pipeline-orchestration                       | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ⬜     |  ⬜   |
| [pipeline-orchestration](steps/pipeline-orchestration.md)             | stream-endpoint                              | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ⬜     |  ⬜   |
| [stream-endpoint](steps/stream-endpoint.md)                           | frontend-streaming                           | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ⬜     |  ⬜   |
| [fe-stream-utils](steps/fe-stream-utils.md)                           | fe-evaluate-page                             | —               |     ✅     |   ⚠️   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [fe-evaluate-page](steps/fe-evaluate-page.md)                         | —                                            | —               |     ✅     |   ⚠️   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [fe-results-buckets](steps/fe-results-buckets.md)                     | —                                            | —               |     ✅     |   ⚠️   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [evaluator-prompt-tighten](#evaluator-prompt-tighten)                 | —                                            | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [fe-streaming-ux](#fe-streaming-ux)                                   | —                                            | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

## Per-Cycle Workflow (MANDATORY)

Every cycle in every step follows this exact sequence. No batching, no skipping.

```
1. RED       — Write failing tests. Run them. Confirm they fail for the right reason.
2. GREEN     — Write minimum code to pass. Run ALL tests. Confirm all pass.
               → UPDATE PLAN: mark Auto Tests column (✅ or ❌)
               → COMMIT (tests + code + plan update)
3. REFACTOR  — Clean up if needed.
               → COMMIT if anything changed
4. VERIFY    — Prove it works (curl, DB inspect, run command, etc.)
               → UPDATE PLAN: mark Verify column (✅, ❌, or ➖)
               → COMMIT plan update
5. SIMPLIFY  — Reduce unnecessary complexity. Fix if needed.
               → UPDATE PLAN: mark Simplify column (✅ or ❌)
               → COMMIT plan update (+ code changes if any)
6. REVIEW    — Check for bugs, edge cases, error handling. Fix if needed.
               → UPDATE PLAN: mark Review column (✅ or ❌)
               → COMMIT plan update (+ code changes if any)
```

Each plan update gets its own commit so progress is visible in real time.

- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High. Low on any file → ❌.
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding. Do not mark Human ✅ while any prior column is ❌ without explicit user instruction.

---

## Parallelism Opportunities

```
Phase 1 (parallel):  playbook-parser | schema-migration | agent-core
Phase 2 (parallel):  contract-verifier | clause-splitter | clause-evaluator | headline-synthesis
Phase 3 (sequential): pipeline-orchestration
Phase 4 (sequential): stream-endpoint
Phase 5 (parallel):  fe-stream-utils + fe-evaluate-page | fe-results-buckets
```

Phase 1 steps have no dependencies on each other. Phase 2 steps each depend on agent-core
(and splitter/evaluator also depend on playbook-parser), but are independent of each other.
Phase 5: fe-stream-utils + fe-evaluate-page are coupled (page needs the reader), run as one
agent. fe-results-buckets is independent, runs as a separate agent.

## Post-Merge Workflow (MANDATORY)

**Worktree agents handle only: RED → GREEN → COMMIT (Auto Tests).**

Verify, Simplify, and Review are **skills that produce reports**. They CANNOT be self-reported
by agents — they must run in the main session after merging worktree branches.

After merging parallel agents:
1. Run `/verify` — produces `docs/<feature>/verify/<step>-<date>.md`
2. Run `/simplify` — 3 parallel review agents, fix findings, commit
3. Run `/review` — 3 parallel review agents, fix findings, produces `docs/<feature>/reviews/<step>-<date>.md`
4. Update plan dashboard with real results

Agents marking their own Verify/Simplify/Review columns is **not valid**. Only the main
session running the actual skills can mark those columns.

---

## Branching Strategy

**Single feature branch** — `feat/agentic-eval-pipeline`. The steps are tightly coupled
(they share types, models, and the orchestrator wires them all together). Per-step branches
would create merge friction without benefit. Each step produces one or more commits on the
feature branch.

---

## Steps

### playbook-parser

Parses the 132-check playbook markdown file into structured data. Provides a `get_playbook()`
lookup function that takes agreement type + check names and returns matching checks. Validates
all 132 checks parsed at startup. Done when all 4 agreement types parse correctly and lookups
return exact matches.
[→ Detailed plan](steps/playbook-parser.md)

### schema-migration

Alembic migration adding new columns to `ContractReview` (`agreement_type`) and `ReviewClause`
(`status`, `severity`, `playbook_status`, `playbook_position`, `contract_language`, `finding`,
`recommended_redline`, `relevant_checks`, `cross_references`, `is_cycle`, `is_synthetic`).
Updates ORM models and Pydantic schemas. Updates the status state machine. Done when migration
runs cleanly and models reflect the new schema.
[→ Detailed plan](steps/schema-migration.md)

### agent-core

Base agent runner that wraps the Anthropic SDK: sends messages with tools, handles the tool-use
loop (call → execute tool → respond → repeat until text/end_turn), retries up to 2x on failure,
respects per-agent model config and token budgets, tracks `max_tokens` stop reasons. Done when
the runner can execute a simple tool-using agent with mocked Anthropic responses.
[→ Detailed plan](steps/agent-core.md)

### contract-verifier

Lightweight agent that confirms an upload is a contract. Uses a cheap model, 1024 max tokens.
Returns `{is_contract: bool, reason: str | null}` via tool call. Done when it correctly
classifies contracts vs. non-contracts with mocked LLM responses.
[→ Detailed plan](steps/contract-verifier.md)

### clause-splitter

Agent that reads the full contract, determines agreement type, splits into clauses with
section numbers (synthetic if unnumbered), tags each clause with relevant playbook check names
from the known enum, detects cross-references and cycles. Done when it produces well-formed
`report_clauses` tool output and absent check detection works.
[→ Detailed plan](steps/clause-splitter.md)

### clause-evaluator

Agent that evaluates a single clause against playbook checks. Calls `get_playbook` tool to
retrieve relevant checks, then calls `report_evaluation` tool with the dual-tier rating.
Receives depth-1 cross-referenced clause text. Done when it produces correct evaluations
with mocked LLM responses and handles the get_playbook → report_evaluation tool sequence.
[→ Detailed plan](steps/clause-evaluator.md)

### headline-synthesis

Headline generator agent that receives full evaluation data and produces summary +
call_to_action via tool call. Plus the deterministic synthesis function that computes
`overall_fairness` (worst-clause-wins + 20% escalation), assembles the final result, and
excludes errored clauses. Done when synthesis correctly handles all rating combinations and
the headline agent produces structured output.
[→ Detailed plan](steps/headline-synthesis.md)

### pipeline-orchestration

Wires all agents into the full pipeline: verify → split → persist clauses → evaluate (parallel,
max 7, semaphore) → headline → synthesis → persist results. Includes the NDJSON event emitter
that produces all stream event types. Handles failure semantics (2x retry at agent-core level,
>10% real clause failure → pipeline failure). Uses DB UUIDs for clause row updates. Propagates
user instructions to all agents. Done when the full pipeline runs end-to-end with mocked LLM
responses and emits correct NDJSON events.
[→ Detailed plan](steps/pipeline-orchestration.md)

### stream-endpoint

`GET /api/reviews/{id}/stream` FastAPI endpoint that returns a `StreamingResponse` with
`application/x-ndjson` content type. Triggers the pipeline orchestrator and yields NDJSON
events as they're produced. Handles review-not-found, already-completed, and in-progress
states. Done when the endpoint streams events end-to-end via httpx test client.
[→ Detailed plan](steps/stream-endpoint.md)

### fe-stream-utils

New Zod schemas for all NDJSON streaming events (clean break from polling schemas) and an
NDJSON stream reader utility that parses a ReadableStream into typed events. Done when all
event types validate and the reader correctly handles partial line buffering.

Files: `frontend/app/evaluate-contract/stream-types.ts`, `frontend/app/evaluate-contract/stream.ts`
Tests: `frontend/__tests__/stream.test.ts`, `frontend/__tests__/stream-types.test.ts`

### fe-evaluate-page

Update the evaluate-contract page to consume the NDJSON stream after upload. Uploads with
`stream=true`, opens `GET /api/reviews/{id}/stream`, shows status messages, renders clauses
incrementally, handles rejected/failed events. Done when the page shows streaming progress.

Files: `frontend/app/evaluate-contract/page.tsx`, `frontend/app/evaluate-contract/constants.ts`
Tests: `frontend/__tests__/evaluate-contract-page.test.tsx` (update existing)

### fe-results-buckets

Update the results page to group clauses by fairness tier (dealbreaker → non-standard → fair)
instead of the current grouping. Show severity score on each clause card. Done when clauses
render in severity-tier buckets with scores.

Files: `frontend/app/contract/[id]/page.tsx`, `frontend/app/contract/[id]/ClauseSection.tsx`
Tests: `frontend/__tests__/contract-results-page.test.tsx` (update existing)

### evaluator-prompt-tighten

Minimize token usage in evaluator output. Free-form text fields are too verbose — the LLM
returns paragraphs when we want scores and one-liners. Changes:

- **Evaluator prompt**: instruct "1 sentence max" for `finding`, `explanation`, `purpose`,
  `market_standard`, `recommended_redline`. Emphasize scores (`severity`, `fairness`,
  `playbook_status`) over prose.
- **Evaluator tool schema**: tighten `description` fields to reinforce brevity
  (e.g., "One sentence. Max 20 words.")
- **Headline prompt**: same treatment — summary should be 1-2 sentences, call_to_action
  items should be brief action phrases not paragraphs

Done when evaluator output is measurably shorter (before/after token comparison on a test
contract).

Files: `backend/services/agents/evaluator.py`, `backend/services/agents/headline.py`

### fe-streaming-ux

Replace the current shimmer-based loading with a streaming-aware UI that shows real-time
pipeline progress:

1. **Background shimmer**: subtle shimmer/pulse on the page background instead of placeholder
   cards. The page itself feels "alive" while processing.
2. **Status tracker**: show the current pipeline stage with a progress indicator
   (Verifying → Splitting → Evaluating N/M → Generating summary → Complete)
3. **Clause accumulation**: as `clause_evaluated` events arrive, render actual clause cards
   incrementally — grouped into severity-tier buckets (dealbreaker → non-standard → fair).
   New clauses animate in.
4. **Clause counter**: "Evaluated 3 of 12 clauses" with a progress bar or counter
5. **Bucket headers**: show bucket headers immediately after splitting event (with counts
   updating as clauses arrive)

The key insight: the evaluate page should progressively transform from "waiting" to "results"
as events arrive — not stay in a loading state until everything finishes, then navigate away.

Files: `frontend/app/evaluate-contract/page.tsx`, new components as needed
Tests: `frontend/__tests__/evaluate-contract-page.test.tsx` (update)
