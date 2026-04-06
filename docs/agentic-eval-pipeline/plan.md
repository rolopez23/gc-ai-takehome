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
| [rate-limit-resilience](#rate-limit-resilience)                       | —                                            | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [prompt-tighten](#prompt-tighten)                                     | —                                            | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [fe-stream-context](#fe-stream-context)                               | fe-stream-live-ui                            | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [fe-stream-live-ui](#fe-stream-live-ui)                               | —                                            | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |

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
Phase 6 (parallel):  rate-limit-resilience | prompt-tighten
Phase 7 (sequential): fe-stream-context
Phase 8 (sequential): fe-stream-live-ui
```

Phases 1-5: complete (backend pipeline + initial frontend).
Phase 6: backend fixes (rate limits + prompt brevity) — independent, parallel.
Phase 7-8: frontend streaming UX — context first, then UI on top.

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

### rate-limit-resilience

Fix rate limiting failures caused by blowing the 50K **input** tokens/min Haiku limit. The
splitter sends the full contract, then evaluators each send clause text + playbook checks +
cross-refs. With 7 concurrent evaluators, the input token burst exceeds the limit immediately.

1. **Lower concurrency**: `MAX_CONCURRENT_EVALUATORS` from 7 → 3 (env-configurable via
   `MAX_CONCURRENT_EVALUATORS` env var). Reduces input token burst.
2. **429-specific retry**: distinguish rate limit errors (HTTP 429) from other API errors.
   Retry up to 3 times with longer backoff (10s, 20s, 30s). Log the retry-after header
   if present. Other API errors keep the existing 2x retry with exponential backoff.
3. **Configurable concurrency**: `int(os.getenv("MAX_CONCURRENT_EVALUATORS", "3"))`

Done when a 4-clause contract evaluates without hitting rate limit failures.

Files: `backend/services/agents/base.py`, `backend/services/orchestrator.py`
Tests: `backend/tests/test_agent_base.py` (add 429 retry tests)

### prompt-tighten

Minimize token usage across all agent prompts. Text should be 1 sentence max — we want
scores, not essays.

1. **Evaluator prompt**: instruct "1 sentence max" for `finding`, `explanation`, `purpose`,
   `market_standard`, `recommended_redline`. Emphasize scores over prose.
2. **Evaluator tool schema descriptions**: reinforce brevity ("One sentence. Max 20 words.")
3. **Headline prompt**: summary 1-2 sentences, call_to_action items are brief action phrases
4. **Splitter prompt**: keep clause text verbatim but tighten instructions

Done when evaluator output is measurably shorter on a test contract.

Files: `backend/services/agents/evaluator.py`, `backend/services/agents/headline.py`,
       `backend/services/agents/splitter.py`

### fe-stream-context

Extract streaming state into a React context/hook that maps NDJSON events into clean
component state. This is the data layer — no UI changes.

The context tracks:
- `stage`: "idle" | "verifying" | "splitting" | "evaluating" | "summarizing" | "completed" | "failed" | "rejected"
- `agreementType`: string | null
- `totalClauses`: number (from splitting event)
- `evaluatedCount`: number (increments on each clause_evaluated)
- `failedCount`: number
- `clauses`: StreamClause[] (accumulated from clause_evaluated events)
- `lastClause`: StreamClause | null (most recently evaluated)
- `buckets`: { dealbreaker: StreamClause[], nonStandard: StreamClause[], fair: StreamClause[] }
- `summary`: string (from replace event)
- `callToAction`: string[] (from replace event)
- `error`: string | null (from rejected/failed)
- `reviewId`: string
- `contractId`: string

The hook `useContractStream(reviewId)` calls the stream endpoint and dispatches
events into this state via a reducer. Components consume the context.

Done when the context correctly tracks all state transitions for a mocked event sequence.

Files: `frontend/app/evaluate-contract/StreamContext.tsx` (new)
Tests: `frontend/__tests__/stream-context.test.tsx` (new)

### fe-stream-live-ui

Build the streaming-aware evaluate page UI using the stream context. Minimal, informative,
real-time.

Layout during streaming:
1. **Background shimmer** — subtle pulse on the page background (not placeholder cards).
   Signals "processing" without clutter.
2. **Stage headline** — top of page, updates in real-time:
   "Verifying document..." → "Splitting into N clauses..." →
   "Evaluating clauses (3/12)..." → "Generating summary..." → "Complete"
3. **Top-level stats** — updated in real-time as clauses arrive:
   - Dealbreaker count / Non-standard count / Fair count
   - Severity score badges accumulating
4. **Last clause preview** — shows the most recently evaluated clause (1 at a time,
   replaces the previous). Shows clause type, fairness badge, severity, and 1-sentence
   finding. Animates in/out as new clauses arrive.
5. **On complete** — navigate to `/contract/{id}` results page with full data.

On rejected: show rejection reason with a "Try another contract" button.
On failed: show error with retry option.

Done when uploading a contract shows live streaming progress with stats updating and
clause previews appearing.

Files: `frontend/app/evaluate-contract/page.tsx` (rewrite streaming section),
       `frontend/app/evaluate-contract/ClausePreview.tsx` (new),
       `frontend/app/evaluate-contract/StreamProgress.tsx` (new)
Tests: `frontend/__tests__/evaluate-contract-page.test.tsx` (update)
