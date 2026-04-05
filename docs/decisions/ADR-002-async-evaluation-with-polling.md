# ADR-002: Async Evaluation with Polling

## Status
Accepted

## Date
2026-04-05

## Context
Contract evaluation via Claude takes 10-30 seconds. The frontend needs a strategy for handling
this latency. The backend already has a `ContractReview` model with `status`
(pending/running/completed/failed) and `completed_at` fields, suggesting async was the original
design intent.

## Decision
Use async evaluation with client-side polling.

### Flow
1. Frontend `POST /api/contracts/upload` — sends file via multipart form data
2. Backend saves contract, creates a review with `status=pending`, returns `contract_id` + `review_id`
3. Backend kicks off evaluation in a background task (updates status to `running`)
4. Frontend polls `GET /api/reviews/{review_id}` on an interval until `status` is `completed` or `failed`
5. On `completed`, frontend fetches full results and displays them

### Polling details
- Interval: start at 2s, no need for backoff given the 10-30s typical response time
- Frontend shows a loading/progress state while polling
- Timeout: frontend gives up after ~120s and shows an error

## Alternatives Considered

### Synchronous (block until done)
- **Pros**: Simplest implementation, no polling logic
- **Cons**: 10-30s HTTP request feels broken to users, risk of gateway timeouts, no ability to show progress or recover from disconnection
- **Rejected**: Poor UX and fragile for long-running requests

### WebSockets
- **Pros**: Real-time push, no wasted requests
- **Cons**: Heavy infrastructure for a single status update, connection management complexity, doesn't add meaningful value over polling for this use case
- **Rejected**: Overkill — polling is sufficient when you're waiting for one state transition

## Consequences
- Backend needs a background task mechanism (FastAPI `BackgroundTasks` or similar)
- Frontend needs a polling hook/utility
- Review status transitions must be atomic and correct (pending → running → completed/failed)
- The existing `ContractReview.status` and `completed_at` fields support this with no schema changes
