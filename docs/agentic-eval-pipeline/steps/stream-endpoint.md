# Step: stream-endpoint

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)
>
> Depends on: pipeline-orchestration

## What This Step Delivers

A `GET /api/reviews/{id}/stream` FastAPI endpoint that returns a `StreamingResponse` with
`application/x-ndjson` content type. Triggers the pipeline orchestrator and yields NDJSON
events as they're produced. Handles edge cases: review not found, already completed, already
in progress.

## Done When

- `GET /api/reviews/{id}/stream` returns streaming NDJSON
- Content-Type is `application/x-ndjson`
- Review not found returns 404
- Already-completed review returns 409 (or similar)
- The pipeline runs in the streaming response context
- Existing upload and polling endpoints remain unchanged

## Cycles

### stream-endpoint-happy-path

**Test** — write these tests and confirm they fail:
- **test_stream_endpoint_returns_ndjson**: `GET /api/reviews/{id}/stream` returns status 200
  with content-type `application/x-ndjson`
- **test_stream_endpoint_emits_events**: response body contains NDJSON lines starting with
  `{"event":"started"...}` and ending with `{"event":"completed"...}`
- **test_stream_endpoint_review_not_found**: `GET /api/reviews/{bad_id}/stream` returns 404

**Code** — add to `backend/routers/reviews.py`:

```python
from fastapi.responses import StreamingResponse

@router.get("/{review_id}/stream")
async def stream_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    review = await db.get(ContractReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    contract = await db.get(
        Contract, review.contract_id,
        options=[undefer(Contract.pdf_blob)],
    )

    orchestrator = PipelineOrchestrator(
        review_id=review.id,
        contract_id=contract.id,
        instructions=review.review_instructions,
    )

    return StreamingResponse(
        orchestrator.run(),
        media_type="application/x-ndjson",
    )
```

**Refactor** — none

**Commit**: `add GET /api/reviews/{id}/stream NDJSON endpoint`

---

### stream-endpoint-edge-cases

**Test** — write these tests and confirm they fail:
- **test_stream_already_completed**: review with `status="completed"` → returns 409
  "Review already completed"
- **test_stream_already_rejected**: review with `status="rejected"` → returns 409
- **test_stream_already_in_progress**: review with `status="evaluating"` → returns 409
  "Review already in progress"
- **test_existing_upload_endpoint_unchanged**: `POST /api/contracts/upload` still works
  and returns the same JSON shape
- **test_existing_polling_endpoint_unchanged**: `GET /api/reviews/{id}` still works

**Code** — add status checks before starting the pipeline:

```python
if review.status in ("completed", "failed", "rejected"):
    raise HTTPException(status_code=409, detail="Review already completed")
if review.status not in ("pending",):
    raise HTTPException(status_code=409, detail="Review already in progress")
```

**Refactor** — none

**Commit**: `add stream endpoint edge case handling`

---

## Verification

```bash
cd backend && uv run pytest tests/test_stream_endpoint.py -v
```

Then manually test with curl:

```bash
# Upload a contract first
curl -s -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@test_contract.pdf" | jq .

# Stream the evaluation (replace REVIEW_ID)
curl -N http://localhost:8000/api/reviews/REVIEW_ID/stream
```

Expected: curl shows NDJSON lines appearing one at a time as the pipeline progresses.
Each line is valid JSON. The stream ends with a `completed` or `failed` event.
