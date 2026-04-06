# Spec: Agentic Contract Evaluation Pipeline

## Problem Statement

The contract evaluation pipeline currently makes a single LLM call against the entire contract,
producing a monolithic JSON response. This means no guaranteed structure per clause, no granular
progress feedback (the frontend polls a status field), no parallelism, and no grounding against the
132-check playbook. The result is slow, fragile, and opaque to the user.

## What We Are Solving

- **Agentic orchestration**: Replace the single LLM call with a multi-agent pipeline:
  Contract Verifier -> Clause Splitter -> parallel Clause Evaluators -> Headline Generator ->
  Deterministic Synthesis.
- **Contract verification gate**: A lightweight, cheap-model agent that confirms the upload is
  a contract before the pipeline spends tokens on splitting and evaluation.
- **Playbook grounding via tool calls**: The Clause Splitter identifies the agreement type and
  tags each clause with relevant playbook check names (constrained to a known enum of valid
  names, provided in the prompt with one-sentence descriptions). Clause evaluator agents call a
  `get_playbook` tool using those tags to retrieve the exact checks, grounding evaluation against
  the 132-check playbook (`docs/gc-ai-takehome/gc_ai_playbook.md`).
- **Absent check detection (deterministic)**: After splitting, the orchestrator (not the LLM)
  compares tagged checks against the full check list for the detected agreement type. Uncovered
  checks become synthetic ABSENT clauses handled deterministically — no LLM evaluator call.
  Importance maps to severity: High→8/dealbreaker, Medium→5/non-standard, Low→2/fair.
- **Dual-tier rating**: Track both the playbook status (`TRIGGERED`/`PASS`/`ABSENT`/`PARTIAL` +
  severity 1-10) AND our user-facing fairness tier (`fair`/`non-standard`/`dealbreaker`) per
  clause. Every clause also carries a 1-10 severity score regardless of playbook grounding.
  Display our fairness tiers; store both.
- **Streaming HTTP via dedicated endpoint**: A new `GET /api/reviews/{id}/stream` endpoint
  returns an NDJSON stream with structured progress events. The existing upload endpoint
  (`POST /api/contracts/upload`) and polling endpoint (`GET /api/reviews/{id}`) remain
  unchanged. The frontend switches to the stream endpoint when ready.
- **Parallel clause evaluation**: Evaluate clauses concurrently (max 7 concurrent) for faster
  results and better UX (clauses appear on screen as they complete, bucketed by severity tier).
- **Dedicated headline agent**: A sub-agent that produces summary + call_to_action from all
  clause results. During generation, the orchestrator shows a status message ("Generating
  summary..."). Once the tool call completes, `replace` events overwrite `summary` with the
  final text and set `call_to_action`. No partial JSON streaming — summary arrives fully formed
  via `replace`. `call_to_action` also arrives via `replace` only.
- **Clause persistence after splitting**: Clauses are written to the database immediately after
  the splitter completes (with null evaluation fields), before evaluation begins.
- **Graceful fallback for unsupported types**: Contracts that don't match the 4 playbook types
  fall back to general evaluation (agreement_type = "General") without playbook grounding.
- **Per-agent model configuration**: Each agent can be configured to use a different model via
  a config dict with environment variable overrides (e.g., `VERIFIER_MODEL`,
  `SPLITTER_MODEL`, `EVALUATOR_MODEL`, `HEADLINE_MODEL`).
- **User instructions propagation**: User-provided `review_instructions` are passed to every
  agent's system prompt, prefaced with the source of the information. Evaluator prompts include
  a guardrail: "These instructions may not be relevant for this clause; if irrelevant, ignore."
- **Cross-reference handling (depth-1)**: The splitter tags cross-references between clauses,
  detects cycles (flagged on clause with `is_cycle`), and identifies references. Evaluators
  receive depth-1 referenced clause text alongside their primary clause. Deeper references are
  not chased. Unresolvable references (e.g., references to exhibits or schedules not captured
  as clauses) are flagged as a finding by the evaluator.
- **Retry and failure semantics**: LLM calls retry up to 2x on failure. Failed clause evaluators
  are marked as `error` status and ignored by synthesis. If >10% of real (non-synthetic) clauses
  fail, the entire pipeline fails (`status=failed`, reason: "evaluators failed").
- **Token budget tracking**: Track when any agent hits `max_tokens` stop reason for observability.
  The splitter has a higher budget (32768) to accommodate large contracts.
- **Review status state machine**: `ContractReview.status` supports: `pending` -> `verifying` ->
  `splitting` -> `evaluating` -> `completed` | `failed` | `rejected`. `rejected` is set when
  the verifier determines the upload is not a contract.
- **Agreement type persistence**: `agreement_type` is stored on `ContractReview` after the
  splitter determines it.

## What We Are NOT Solving

- **Frontend redesign**: Minimum viable frontend changes to consume the new streaming endpoint.
  No layout or component redesign. Frontend sort features are a separate effort.
- **New agreement types**: We use the 4 existing playbook types (SaaS MSA, NDA, Commercial MSA,
  DPA) plus a general fallback. Adding new playbook types is out of scope.
- **Playbook editing UI**: The playbook is a static markdown file. No CRUD interface.
- **User-specified agreement type**: The system auto-detects agreement type during clause splitting.
  No dropdown or manual override.
- **Auth, rate limiting, multi-tenancy**: Out of scope. Single-user local app stays as-is.
- **Stream disconnection recovery**: If the client disconnects mid-stream, evaluation continues
  server-side and results are persisted. The user sees the completed contract on the home page.
  Reconnection / event replay is a TODO.
- **Deep cross-reference resolution**: Only depth-1 references are resolved. Transitive
  references (references of references) are out of scope.

## Actors & Triggers

| Actor | Role |
|-------|------|
| **User** | Uploads a contract file via the frontend |
| **Backend orchestrator** | Receives the upload, drives the agent pipeline, streams events. Uses DB UUIDs (not section numbers) to identify clause rows for updates |
| **Contract Verifier agent** | Lightweight, cheap-model gate: confirms the upload is a contract. Emits `rejected` if not. Sets `ContractReview.status=rejected` |
| **Clause Splitter agent** | Reads full contract (PDF document block or plain text — handles both modalities), determines agreement type, splits into clauses, tags each clause with relevant playbook check names (from enum), flags cross-references, detects cycles |
| **Orchestrator (deterministic)** | After splitting: compares tagged checks against full playbook, generates synthetic ABSENT clauses with deterministic ratings, persists all clauses to DB |
| **Clause Evaluator agent** (max 7 concurrent) | Evaluates one real clause against playbook checks via tool call. Receives depth-1 cross-referenced clause text when flagged by the splitter. Flags unresolvable references as findings |
| **Headline Generator agent** | Receives: `agreement_type`, full evaluation data for all successfully evaluated clauses, count of failed clauses, count of synthetic ABSENT clauses. Produces summary + call_to_action |
| **Synthesis function** (deterministic code) | Combines all clause evaluations + headline into final structured result. Computes `overall_fairness` deterministically |
| **Frontend** | Consumes the NDJSON stream, renders clauses incrementally in severity-tier buckets |

**Trigger flow**:
1. `POST /api/contracts/upload` — unchanged, returns `{contract_id, review_id, status}`, spawns
   background evaluation pipeline
2. `GET /api/reviews/{id}/stream` — new endpoint, returns NDJSON stream of evaluation progress
3. `GET /api/reviews/{id}` — unchanged, returns persisted results for the results page

## Success Criteria

1. A new `GET /api/reviews/{id}/stream` endpoint returns an NDJSON stream with events: `started`,
   `token`, `verifying`, `splitting`, `clause_evaluated`, `clause_error`, `replace`,
   `rejected`, `failed`, `completed`.
2. The `started` event includes empty `summary` and `call_to_action` fields. `token` events
   stream status messages (not partial content). `replace` events overwrite fields with finalized
   content. `call_to_action` only arrives via `replace`, never via `token`.
3. A lightweight Contract Verifier agent gates the pipeline before the splitter runs. Non-contract
   uploads receive a `rejected` event with a reason string. `ContractReview.status` is set to
   `rejected`.
4. The Clause Splitter produces check names constrained to the known enum of valid playbook check
   names (provided in its prompt with one-sentence descriptions). `get_playbook` performs
   exact-match lookups; zero-match returns an error.
5. Uncovered playbook checks are handled deterministically by the orchestrator as synthetic ABSENT
   clauses: High importance→severity 8/dealbreaker, Medium→severity 5/non-standard, Low→severity
   2/fair. No LLM evaluator calls for ABSENT clauses.
6. Clause evaluations run in parallel (max 7 concurrent) — wall-clock time scales sub-linearly
   with clause count.
7. Each clause carries both playbook status (`TRIGGERED`/`PASS`/`ABSENT`/`PARTIAL`) and fairness
   tier (`fair`/`non-standard`/`dealbreaker`), plus a 1-10 severity score on every clause
   regardless of playbook grounding. Frontend displays fairness tier in severity-tier buckets
   (dealbreaker -> non-standard -> fair).
8. The final `completed` event contains the full synthesized result. New Zod schemas are created
   for the streaming API (clean break from polling schemas).
9. Results are persisted to the database with both rating schemes. Clauses are persisted
   immediately after splitting, before evaluation begins. `agreement_type` is persisted on
   `ContractReview`.
10. Contracts that don't match a playbook type are evaluated as "General" (no playbook grounding)
    rather than failing.
11. User-provided `review_instructions` are propagated to every agent, prefaced with their source.
    Evaluator prompts include a relevance guardrail.
12. LLM calls retry up to 2x on failure. Failed clauses are marked `error` and ignored by
    synthesis. If >10% of real (non-synthetic) clauses fail, pipeline fails with `status=failed`.
13. Cross-references are tagged by the splitter (depth-1 only, cycles detected and flagged).
    Evaluators receive referenced clause text. Unresolvable references (to exhibits, schedules,
    etc. not captured as clauses) are flagged as findings.
14. Contracts without section numbering receive synthetic sequential identifiers (`clause-1`, etc.).
15. The existing upload and polling endpoints remain unchanged and functional.
16. Token budget overruns (`max_tokens` stop reason) are tracked for observability.
17. Existing tests are updated or replaced to cover the new pipeline.
18. Playbook parser validates 132 checks across 4 agreement types at startup.

## Interfaces

### Schemas

#### Contract Verifier Output (new — enforced via tool call)

```
Tool: verify_contract
Parameters:
  is_contract: bool             # true if the document is a contract
  reason: str | null            # explanation if not a contract, null otherwise
```

Runs on a cheap/fast model. Does not read the full document deeply.

#### Clause Splitter Output (new — enforced via tool call)

```
Tool: report_clauses
Parameters:
  agreement_type: str          # one of: "SaaS MSA", "NDA", "Commercial MSA", "DPA", "General"
  clauses: list[object]
    section_number: str         # e.g. "4.2", or "clause-1" if contract lacks numbering
    clause_type: str            # e.g. "Limitation of Liability"
    text: str                   # exact quoted clause text
    relevant_checks: list[str]  # playbook check names from the known enum
                                # empty list if agreement_type is "General"
    cross_references: list[str] # section numbers this clause references, e.g. ["8.2", "3.1"]
                                # empty list if none
    is_cycle: bool              # true if this clause is part of a reference cycle
```

The splitter's system prompt includes the full list of valid playbook check names with a
one-sentence description of when each applies. The splitter may only use names from this list.
The splitter handles both PDF document blocks and plain text input.

After the splitter returns, the **orchestrator** (deterministic code, not the LLM) compares all
tagged check names against the full check list for the detected agreement type. Uncovered checks
become synthetic ABSENT clauses with deterministic ratings — they do not go through the evaluator.

#### Clause Evaluator Output (new — enforced via tool call)

```
Tool: report_evaluation
Parameters:
  section_number: str
  clause_type: str
  # Severity (always present, 1-10)
  severity: int                 # 1-10, present on every clause regardless of playbook grounding
  # Playbook rating (tracked, not displayed; all null when no playbook grounding)
  playbook_status: "TRIGGERED" | "PASS" | "ABSENT" | "PARTIAL" | null
  playbook_position: str | null
  contract_language: str | null
  finding: str
  recommended_redline: str | null
  # Our rating (displayed)
  fairness: "fair" | "non-standard" | "dealbreaker"
  purpose: str
  market_standard: str
  explanation: str
```

#### Get Playbook Tool (new — called BY clause evaluator agents)

```
Tool: get_playbook
Parameters:
  agreement_type: str           # from splitter output
  check_names: list[str]        # from clause's relevant_checks
Returns:
  checks: list[object]          # matching checks from the playbook
    check_number: int
    check_name: str
    importance: "High" | "Medium" | "Low"
    key_position: str
Error:
  Returns error if zero checks match (indicates a splitter output problem).
```

The `get_playbook` tool performs exact-match lookups against playbook check names. The Clause
Splitter is responsible for producing correct check names from the known enum; the tool is a
simple data lookup, not a fuzzy matcher.

#### Headline Generator Input (new)

The headline agent receives a structured user message containing:
- `agreement_type: str`
- `clauses: list[ClauseEvaluation]` — full evaluation data for all successfully evaluated clauses
  (matching `report_evaluation` output shape). Excludes errored clauses.
- `failed_clause_count: int`
- `absent_clause_count: int` — count of synthetic ABSENT clauses

#### Headline Generator Output (new — enforced via tool call)

```
Tool: report_headline
Parameters:
  summary: str                  # concise executive summary
  call_to_action: list[str]     # specific next steps for the user
```

During generation, the orchestrator emits a `token` status message ("Generating summary...").
Once the tool call completes, `replace` events overwrite `summary` with the final text and set
`call_to_action`. No partial JSON streaming — both fields arrive fully formed via `replace`.

#### Synthesis Output (deterministic code, not an LLM call)

Combines all clause evaluations (real + synthetic ABSENT) + headline into the final result:

```
overall_fairness: "fair" | "non-standard" | "dealbreaker"
agreement_type: str
summary: str
call_to_action: list[str]
clauses: list[ClauseEvaluation]   # each with both rating schemes + severity
```

`overall_fairness` is computed deterministically: worst individual clause rating wins, with an
escalation rule (configurable threshold: 20%+ non-standard clauses escalate to
dealbreaker). Failed clauses (status=error) are excluded from this computation.

#### Database Changes

`ContractReview` table gains columns:
- `agreement_type`: text, nullable (set after splitter completes)

`ContractReview.status` state machine:
- `pending` -> `verifying` -> `splitting` -> `evaluating` -> `completed` | `failed`
- `pending` -> `verifying` -> `rejected` (not a contract)

`ReviewClause` table gains columns:
- `status`: enum (pending, evaluated, error), default pending
- `severity`: int, nullable (1-10)
- `playbook_status`: enum (TRIGGERED, PASS, ABSENT, PARTIAL), nullable
- `playbook_position`: text, nullable
- `contract_language`: text, nullable
- `finding`: text, nullable
- `recommended_redline`: text, nullable
- `relevant_checks`: JSON array, nullable (check names from splitter)
- `cross_references`: JSON array, nullable (section numbers)
- `is_cycle`: bool, default false
- `is_synthetic`: bool, default false (true for deterministic ABSENT clauses)

Clauses are inserted into the database immediately after the Clause Splitter completes
(with `status=pending` and null evaluation fields). The orchestrator uses the database
primary key (UUID) — not `section_number` — to identify clause rows for updates.
Each evaluator uses its own database session. Failed evaluators set `status=error`.

#### NDJSON Stream Events

```jsonl
{"event":"started","review_id":"uuid","summary":"","call_to_action":[]}
{"event":"token","field":"status","text":"Verifying document..."}
{"event":"verifying","is_contract":true}
{"event":"token","field":"status","text":"Splitting clauses..."}
{"event":"splitting","agreement_type":"SaaS MSA","clause_count":14}
{"event":"token","field":"status","text":"Evaluating clause 3 of 14..."}
{"event":"clause_evaluated","clause":{ <ClauseEvaluation> }}
{"event":"clause_error","section_number":"4.2","clause_type":"...","error":"timeout after 2 retries"}
{"event":"token","field":"status","text":"Generating summary..."}
{"event":"replace","field":"summary","text":"This SaaS agreement contains..."}
{"event":"replace","field":"call_to_action","value":["Negotiate LoL cap...", "..."]}
{"event":"completed","result":{ <full synthesis> }}
{"event":"rejected","reason":"This document appears to be a recipe, not a contract."}
{"event":"failed","reason":"evaluators failed (>10% clause failure rate)"}
```

Notes:
- `token` events stream status messages only (not partial content). `replace` events overwrite
  fields with finalized content.
- `rejected` terminates the stream (non-contract detected by verifier).
- `failed` terminates the stream (pipeline failure, e.g., >10% real clause evaluator failures).
- `clause_evaluated` events arrive in completion order. The frontend renders in severity-tier
  buckets (dealbreaker -> non-standard -> fair), not section order.
- `call_to_action` only arrives via `replace`, never via `token`.

### Contracts

| System | Direction | What |
|--------|-----------|------|
| Anthropic API | Backend -> Anthropic | Multiple `messages.create` calls with `tools` (strict mode), `tool_choice` forcing; per-agent model config |
| Anthropic API | Anthropic -> Backend | Tool-use content blocks with guaranteed schema-adherent structured outputs |
| Streaming HTTP | Backend -> Frontend | Chunked NDJSON on `GET /api/reviews/{id}/stream` |

### Shared State

- `Contract` and `ContractReview` tables (existing, extended) — read by orchestrator, written by
  synthesis. `agreement_type` persisted on `ContractReview`.
- `ReviewClause` table (existing, extended) — written after splitting, updated after evaluation.
  Orchestrator uses UUID primary keys for row identification.
- Playbook markdown file — read-only, parsed at startup with validation (132 checks across 4 types)

### Existing Code

| File | Current Role | Expected Changes |
|------|-------------|-----------------|
| `backend/services/evaluation.py` | Single LLM call + response parsing | Replace with orchestrator driving agent pipeline |
| `backend/prompt.py` | Monolithic system prompt + Pydantic schemas | Split into per-agent prompts with user instructions propagation; tool definitions replace embedded JSON schemas |
| `backend/routers/contracts.py` | Upload endpoint returns JSON, spawns background task | **Unchanged** — keeps spawning background task |
| `backend/routers/reviews.py` | Polling endpoint | Add new `GET /api/reviews/{id}/stream` endpoint alongside existing polling |
| `backend/models.py` | DB models | Add `agreement_type` to `ContractReview`; add new columns to `ReviewClause`; update status enum |
| `frontend/app/evaluate-contract/page.tsx` | Polling logic | Minimum viable changes: add NDJSON stream reader for new endpoint |
| `frontend/app/evaluate-contract/types.ts` | Zod schemas for polling | New Zod schemas for streaming events (clean break) |
| `frontend/app/contract/[id]/page.tsx` | Results display | Minimal changes — severity-tier bucket rendering |
| `docs/gc-ai-takehome/gc_ai_playbook.md` | Reference doc | Parsed as structured data source for `get_playbook` tool |

### Agent Model Configuration

```python
AGENT_MODELS = {
    "verifier": os.getenv("VERIFIER_MODEL", "claude-haiku-4-5-20251001"),
    "splitter": os.getenv("SPLITTER_MODEL", "claude-haiku-4-5-20251001"),
    "evaluator": os.getenv("EVALUATOR_MODEL", "claude-haiku-4-5-20251001"),
    "headline": os.getenv("HEADLINE_MODEL", "claude-haiku-4-5-20251001"),
}
```

### Agent Token Budgets

```python
AGENT_MAX_TOKENS = {
    "verifier": 1024,     # lightweight yes/no
    "splitter": 32768,    # must return full clause text for entire contract
    "evaluator": 8192,    # single clause evaluation
    "headline": 8192,     # summary + call_to_action
}
```

Token budget overruns (`max_tokens` stop reason) are tracked for observability.

### Concurrency

- Max 7 concurrent clause evaluators (bounds both DB connection pool usage and API rate pressure)
- Each evaluator gets its own DB session
- Failure threshold: >10% of real (non-synthetic) clauses → pipeline failure

### API Rate Limits (confirmed)

Account tier limits (Haiku, the default model):
- 50 requests/min
- 50K input tokens/min (excluding cache reads)
- 10K output tokens/min

Sonnet/Opus (if configured per-agent):
- 50 requests/min
- 30K input tokens/min (excluding cache reads)
- 8K output tokens/min

The max-7 concurrent evaluator cap stays well within the 50 RPM limit. The output token limit
(10K/min for Haiku) is the tightest constraint — monitor this for large contracts with many
clauses.

## Resolved Questions

All open questions have been resolved:

1. **Escalation threshold** → 20% of non-standard clauses escalates to dealbreaker. Implemented
   as a configurable constant for easy adjustment.

2. **Anthropic API concurrency limits** → 50 RPM, 50K input/10K output tokens per minute on
   Haiku. Max-7 evaluator cap is safe. Output tokens/min is the bottleneck to watch.
