# Step: pipeline-orchestration

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)
>
> Depends on: all agent steps, schema-migration, playbook-parser

## What This Step Delivers

The orchestrator that wires all agents into the full pipeline: verify → split → persist clauses →
evaluate (parallel, max 7, semaphore) → generate absent clauses → headline → synthesis → persist
results. Includes the NDJSON event emitter that produces all stream event types. Handles failure
semantics and status state machine transitions.

## Done When

- Full pipeline runs end-to-end with mocked LLM responses
- Clauses are persisted to DB after splitting (status=pending)
- Parallel evaluators run with max 7 concurrency via `asyncio.Semaphore`
- Absent clauses are generated deterministically and persisted
- Evaluator results update clause rows using DB UUIDs
- Each evaluator uses its own DB session
- >10% real clause failure triggers pipeline failure
- NDJSON events are emitted at each stage
- User instructions propagated to all agents
- Status transitions: pending → verifying → splitting → evaluating → completed/failed/rejected

## Cycles

### ndjson-event-emitter

**Test** — write these tests and confirm they fail:
- **test_emitter_started_event**: `emitter.started(review_id)` yields
  `{"event":"started","review_id":"...","summary":"","call_to_action":[]}`
- **test_emitter_token_event**: `emitter.token("status", "Reading...")` yields correct JSON
- **test_emitter_clause_evaluated_event**: `emitter.clause_evaluated(clause_data)` yields
  correct JSON
- **test_emitter_replace_event**: `emitter.replace("summary", "Final text")` yields correct JSON
- **test_emitter_rejected_event**: `emitter.rejected("Not a contract")` yields correct JSON
- **test_emitter_failed_event**: `emitter.failed("evaluators failed")` yields correct JSON
- **test_emitter_completed_event**: `emitter.completed(result_dict)` yields correct JSON
- **test_emitter_outputs_ndjson**: each event is a single JSON line ending with `\n`

**Code** — create `backend/services/streaming.py`:

```python
import json

class EventEmitter:
    def __init__(self):
        self._events: list[str] = []

    def _emit(self, event: dict) -> str:
        line = json.dumps(event) + "\n"
        self._events.append(line)
        return line

    def started(self, review_id: str) -> str:
        return self._emit({"event": "started", "review_id": review_id,
                          "summary": "", "call_to_action": []})

    def token(self, field: str, text: str) -> str:
        return self._emit({"event": "token", "field": field, "text": text})

    def verifying(self, is_contract: bool) -> str:
        return self._emit({"event": "verifying", "is_contract": is_contract})

    def splitting(self, agreement_type: str, clause_count: int) -> str:
        return self._emit({"event": "splitting", "agreement_type": agreement_type,
                          "clause_count": clause_count})

    def clause_evaluated(self, clause: dict) -> str:
        return self._emit({"event": "clause_evaluated", "clause": clause})

    def clause_error(self, section_number: str, clause_type: str, error: str) -> str:
        return self._emit({"event": "clause_error", "section_number": section_number,
                          "clause_type": clause_type, "error": error})

    def replace(self, field: str, value) -> str:
        if isinstance(value, str):
            return self._emit({"event": "replace", "field": field, "text": value})
        return self._emit({"event": "replace", "field": field, "value": value})

    def rejected(self, reason: str) -> str:
        return self._emit({"event": "rejected", "reason": reason})

    def failed(self, reason: str) -> str:
        return self._emit({"event": "failed", "reason": reason})

    def completed(self, result: dict) -> str:
        return self._emit({"event": "completed", "result": result})
```

**Refactor** — none

**Commit**: `add NDJSON event emitter for all stream event types`

---

### orchestrator-verify-stage

**Test** — write these tests and confirm they fail:
- **test_orchestrator_rejects_non_contract**: mock verifier to return `is_contract=False`.
  Pipeline emits `rejected` event, sets `review.status="rejected"`, stops.
- **test_orchestrator_passes_contract**: mock verifier to return `is_contract=True`.
  Pipeline continues past verification.
- **test_orchestrator_emits_verifying_event**: pipeline emits `verifying` event after
  verification.
- **test_orchestrator_sets_status_verifying**: `review.status` is set to "verifying" before
  calling verifier.

**Code** — create `backend/services/orchestrator.py`:

```python
class PipelineOrchestrator:
    def __init__(self, review_id: uuid.UUID, contract_id: uuid.UUID,
                 instructions: str | None = None):
        self.review_id = review_id
        self.contract_id = contract_id
        self.instructions = instructions
        self.emitter = EventEmitter()

    async def run(self) -> AsyncGenerator[str, None]:
        yield self.emitter.started(str(self.review_id))

        # Stage 1: Verify
        yield self.emitter.token("status", "Verifying document...")
        async with AsyncSessionLocal() as db:
            review = await db.get(ContractReview, self.review_id)
            review.status = "verifying"
            await db.commit()

        verifier = VerifierAgent(instructions=self.instructions)
        result = await verifier.run(pdf_blob=..., text=...)

        yield self.emitter.verifying(result.is_contract)

        if not result.is_contract:
            async with AsyncSessionLocal() as db:
                review = await db.get(ContractReview, self.review_id)
                review.status = "rejected"
                review.summary = result.reason
                review.completed_at = datetime.now(UTC)
                await db.commit()
            yield self.emitter.rejected(result.reason)
            return
        ...
```

**Refactor** — none

**Commit**: `add orchestrator verification stage with rejected flow`

---

### orchestrator-split-and-persist

**Test** — write these tests and confirm they fail:
- **test_orchestrator_splits_contract**: mock splitter to return 5 clauses. Pipeline emits
  `splitting` event with correct clause count.
- **test_orchestrator_persists_clauses**: after splitting, 5 `ReviewClause` rows exist in DB
  with `status="pending"` and null evaluation fields.
- **test_orchestrator_persists_agreement_type**: `ContractReview.agreement_type` is set.
- **test_orchestrator_sets_status_splitting**: `review.status` transitions to "splitting".
- **test_orchestrator_persists_absent_clauses**: for a SaaS MSA with 15 of 21 checks tagged,
  6 synthetic absent clauses are also persisted with `is_synthetic=True`.

**Code** — add the split stage to the orchestrator. After the splitter returns:
1. Set `review.status = "splitting"`, `review.agreement_type = result.agreement_type`
2. Generate absent clauses via `detect_absent_checks()`
3. Insert all clauses (real + synthetic) into `review_clauses` with `status="pending"`
4. Store the clause DB UUIDs for later update

**Refactor** — none

**Commit**: `add orchestrator split stage with clause and absent check persistence`

---

### orchestrator-parallel-evaluation

**Test** — write these tests and confirm they fail:
- **test_orchestrator_evaluates_clauses_parallel**: mock evaluator to return results for 5
  clauses. All 5 `ReviewClause` rows updated with `status="evaluated"`.
- **test_orchestrator_max_7_concurrency**: mock evaluator with a delay. With 10 clauses,
  confirm only 7 run concurrently (track active count).
- **test_orchestrator_emits_clause_evaluated**: each successful evaluation emits a
  `clause_evaluated` event.
- **test_orchestrator_handles_evaluator_failure**: mock one evaluator to fail. That clause
  gets `status="error"`, `clause_error` event emitted, others still succeed.
- **test_orchestrator_skips_synthetic_clauses**: synthetic ABSENT clauses (is_synthetic=True)
  are NOT sent to the evaluator — they already have deterministic ratings.
- **test_orchestrator_passes_cross_ref_text**: evaluator receives depth-1 referenced clause
  text for clauses with cross_references.

**Code** — add the evaluation stage:

```python
semaphore = asyncio.Semaphore(7)

async def evaluate_clause(clause_row, clause_data, cross_ref_text):
    async with semaphore:
        evaluator = EvaluatorAgent(self.agreement_type, self.instructions)
        try:
            result = await evaluator.run(clause_data, cross_ref_text)
            async with AsyncSessionLocal() as db:
                row = await db.get(ReviewClause, clause_row.id)
                row.status = "evaluated"
                row.severity = result.severity
                row.fairness = result.fairness
                # ... set all fields
                await db.commit()
            return ("ok", clause_row.id, result)
        except Exception as e:
            async with AsyncSessionLocal() as db:
                row = await db.get(ReviewClause, clause_row.id)
                row.status = "error"
                await db.commit()
            return ("error", clause_row.id, str(e))

# Launch all non-synthetic clause evaluations
tasks = [evaluate_clause(row, data, xref) for row, data in real_clauses]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Refactor** — none

**Commit**: `add parallel clause evaluation with max-7 semaphore`

---

### orchestrator-failure-threshold

**Test** — write these tests and confirm they fail:
- **test_orchestrator_fails_on_10_percent**: 10 real clauses, 2 fail (20%) →
  pipeline fails with `status="failed"`
- **test_orchestrator_succeeds_under_threshold**: 10 real clauses, 0 fail → pipeline continues
- **test_orchestrator_threshold_ignores_synthetic**: 5 real + 5 synthetic, 0 real fail →
  pipeline succeeds (synthetic don't count)
- **test_orchestrator_emits_failed_event**: on threshold breach, `failed` event is emitted

**Code** — after all evaluations complete, count real clause failures:

```python
real_clause_count = sum(1 for c in clause_rows if not c.is_synthetic)
failed_count = sum(1 for r in results if r[0] == "error")
if real_clause_count > 0 and failed_count / real_clause_count > 0.10:
    # Pipeline failure
    yield self.emitter.failed("evaluators failed (>10% clause failure rate)")
    return
```

**Refactor** — none

**Commit**: `add >10% real clause failure threshold`

---

### orchestrator-headline-and-synthesis

**Test** — write these tests and confirm they fail:
- **test_orchestrator_runs_headline**: mock headline agent to return summary and call_to_action.
  Pipeline emits `replace` events for both fields.
- **test_orchestrator_emits_status_during_headline**: pipeline emits
  `token("status", "Generating summary...")` before headline agent runs.
- **test_orchestrator_runs_synthesis**: pipeline emits `completed` event with full result
  including `overall_fairness`.
- **test_orchestrator_persists_final_result**: `ContractReview` updated with
  `status="completed"`, `overall_fairness`, `summary`, `call_to_action`.

**Code** — add headline and synthesis stages:

```python
# Headline
yield self.emitter.token("status", "Generating summary...")
headline_agent = HeadlineAgent(instructions=self.instructions)
headline = await headline_agent.run(
    agreement_type=self.agreement_type,
    clauses=evaluated_results,
    failed_clause_count=failed_count,
    absent_clause_count=absent_count,
)
yield self.emitter.replace("summary", headline.summary)
yield self.emitter.replace("call_to_action", headline.call_to_action)

# Synthesis
final = synthesize(self.agreement_type, all_clause_results, headline)
yield self.emitter.completed(final)

# Persist
async with AsyncSessionLocal() as db:
    review = await db.get(ContractReview, self.review_id)
    review.status = "completed"
    review.overall_fairness = final["overall_fairness"]
    review.summary = final["summary"]
    review.call_to_action = final["call_to_action"]
    review.completed_at = datetime.now(UTC)
    await db.commit()
```

**Refactor** — extract DB persistence into helper methods

**Commit**: `add headline generation and synthesis stages to orchestrator`

---

## Verification

```bash
cd backend && uv run pytest tests/test_orchestrator.py -v
```

Expected: all tests pass. Full pipeline runs end-to-end with mocked agents, correct status
transitions, NDJSON events, clause persistence, and failure handling.
