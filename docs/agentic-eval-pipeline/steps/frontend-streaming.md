# Step: frontend-streaming

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)
>
> Depends on: stream-endpoint

## What This Step Delivers

Minimum viable frontend changes: a NDJSON stream reader utility, new Zod schemas for streaming
events (clean break from polling schemas), updated evaluate-contract page to consume the stream
after upload, and severity-tier bucket rendering on the results page. The existing polling flow
continues to work alongside the new streaming flow.

## Done When

- NDJSON stream reader can parse a stream of JSON lines and dispatch events
- Zod schemas validate all streaming event types
- Evaluate-contract page uploads → gets review_id → opens stream → shows progress
- Clauses render incrementally in severity-tier buckets (dealbreaker → non-standard → fair)
- `rejected` and `failed` events display appropriate error states
- Existing polling flow still works (no breaking changes)

## Cycles

### streaming-zod-schemas

**Test** — write these tests and confirm they fail:
- **test_started_event_schema**: `StartedEventSchema.parse(...)` validates correctly
- **test_token_event_schema**: `TokenEventSchema.parse(...)` validates correctly
- **test_clause_evaluated_schema**: `ClauseEvaluatedEventSchema.parse(...)` validates
  with all clause fields including severity and playbook_status
- **test_replace_event_schema**: `ReplaceEventSchema.parse(...)` validates for both
  string (summary) and array (call_to_action) values
- **test_completed_event_schema**: `CompletedEventSchema.parse(...)` validates with
  full result shape
- **test_rejected_event_schema**: `RejectedEventSchema.parse(...)` validates with reason
- **test_streaming_event_union**: `StreamingEventSchema.parse(...)` discriminates correctly
  based on `event` field

**Code** — update `frontend/app/evaluate-contract/types.ts` to add new schemas:

```typescript
// New streaming schemas (clean break from polling schemas)
export const StartedEventSchema = z.object({
  event: z.literal("started"),
  review_id: z.string(),
  summary: z.string(),
  call_to_action: z.array(z.string()),
});

export const TokenEventSchema = z.object({
  event: z.literal("token"),
  field: z.string(),
  text: z.string(),
});

export const ClauseEvaluatedEventSchema = z.object({
  event: z.literal("clause_evaluated"),
  clause: z.object({
    section_number: z.string(),
    clause_type: z.string(),
    severity: z.number(),
    fairness: FairnessRatingSchema,
    purpose: z.string(),
    market_standard: z.string(),
    explanation: z.string(),
    playbook_status: z.string().nullable(),
    playbook_position: z.string().nullable(),
    contract_language: z.string().nullable(),
    finding: z.string(),
    recommended_redline: z.string().nullable(),
  }),
});

// ... etc for all event types

export const StreamingEventSchema = z.discriminatedUnion("event", [
  StartedEventSchema,
  TokenEventSchema,
  VerifyingEventSchema,
  SplittingEventSchema,
  ClauseEvaluatedEventSchema,
  ClauseErrorEventSchema,
  ReplaceEventSchema,
  CompletedEventSchema,
  RejectedEventSchema,
  FailedEventSchema,
]);
```

**Refactor** — none

**Commit**: `add Zod schemas for NDJSON streaming events`

---

### ndjson-stream-reader

**Test** — write these tests and confirm they fail:
- **test_stream_reader_parses_lines**: given a ReadableStream of NDJSON, the reader yields
  parsed objects one at a time
- **test_stream_reader_handles_partial_lines**: buffered chunks that split mid-line are
  reassembled correctly
- **test_stream_reader_validates_events**: each parsed line is validated against
  `StreamingEventSchema`

**Code** — create `frontend/app/evaluate-contract/stream.ts`:

```typescript
export async function* readNDJSONStream(
  response: Response,
): AsyncGenerator<z.infer<typeof StreamingEventSchema>> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop()!; // keep incomplete last line in buffer

    for (const line of lines) {
      if (line.trim()) {
        const parsed = JSON.parse(line);
        yield StreamingEventSchema.parse(parsed);
      }
    }
  }
}
```

**Refactor** — none

**Commit**: `add NDJSON stream reader utility`

---

### evaluate-page-stream-consumer

**Test** — write these tests and confirm they fail:
- **test_evaluate_page_opens_stream**: after upload succeeds, page fetches
  `/api/reviews/{id}/stream` and processes events
- **test_evaluate_page_shows_status**: `token` events with `field="status"` update a
  status display
- **test_evaluate_page_shows_clauses_incrementally**: `clause_evaluated` events add clauses
  to the display one at a time
- **test_evaluate_page_handles_rejected**: `rejected` event shows the rejection reason
- **test_evaluate_page_handles_failed**: `failed` event shows the failure reason
- **test_evaluate_page_navigates_on_complete**: `completed` event navigates to
  `/contract/{id}`

**Code** — update `frontend/app/evaluate-contract/page.tsx`:
Replace the polling flow with stream consumption after upload. The upload still hits
`POST /api/contracts/upload` and gets `{review_id}`. Then instead of polling, open the
stream at `GET /api/reviews/{review_id}/stream`.

```typescript
// After upload
const uploadResult = await uploadContract(file, instructions);
const streamUrl = `${BACKEND_URL}/api/reviews/${uploadResult.review_id}/stream`;
const response = await fetch(streamUrl);

for await (const event of readNDJSONStream(response)) {
  switch (event.event) {
    case "token":
      if (event.field === "status") setStatus(event.text);
      break;
    case "clause_evaluated":
      setClauses(prev => [...prev, event.clause]);
      break;
    case "replace":
      if (event.field === "summary") setSummary(event.text);
      if (event.field === "call_to_action") setCallToAction(event.value);
      break;
    case "completed":
      router.push(`/contract/${contractId}`);
      break;
    case "rejected":
      setError(event.reason);
      break;
    case "failed":
      setError(event.reason);
      break;
  }
}
```

**Refactor** — extract event handler into a separate function

**Commit**: `replace polling with NDJSON stream consumption on evaluate page`

---

### severity-tier-buckets

**Test** — write these tests and confirm they fail:
- **test_results_page_groups_by_severity**: clauses are grouped into buckets:
  dealbreaker, non-standard, fair
- **test_results_page_bucket_order**: dealbreaker bucket appears first, then non-standard,
  then fair
- **test_results_page_shows_severity_score**: each clause card shows its 1-10 severity score

**Code** — update `frontend/app/contract/[id]/page.tsx`:
Change the clause grouping from the current fairness-based grouping to severity-tier buckets.
The grouping logic already exists (lines 29-37 group by fairness) — update to use the
display labels and order: dealbreaker → non-standard → fair.

**Refactor** — none

**Commit**: `add severity-tier bucket rendering on results page`

---

## Verification

```bash
cd frontend && npm test
```

Expected: all frontend tests pass.

Then manual browser verification:

1. Navigate to the evaluate page
2. Upload a contract
3. Observe: status messages appear during verification and splitting
4. Observe: clauses appear one at a time in severity-tier buckets
5. Observe: summary appears after headline generation
6. Observe: navigation to results page on completion
7. Results page shows clauses in severity-tier buckets with severity scores
