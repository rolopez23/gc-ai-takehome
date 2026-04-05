# Spec: Backend-First Contract Evaluation Pipeline (M3)

## Problem Statement
Contract evaluation currently lives entirely in the frontend: the browser reads a .txt file, a
Next.js route handler calls Anthropic, and results are held in React Context — lost on page
refresh. There is no persistence, no support for PDF/DOC/DOCX, and the backend (FastAPI +
PostgreSQL) sits unused. M3 moves the entire pipeline to the backend so evaluations survive
refresh, support real document formats, and lay the foundation for contract history.

## What We Are Solving
- File upload through the backend (multipart form data) supporting PDF, TXT, DOC, DOCX
- Document conversion: DOC/DOCX → PDF via LibreOffice for submission to Claude (see ADR-001)
- Backend calls Anthropic API with the document (PDF as native document block, TXT as text)
- Async evaluation with polling (see ADR-002): upload returns immediately, frontend polls for status
- Granular status progression: pending → reading → evaluating → completed / failed (statuses may be skipped if a phase is trivial, e.g. TXT needs no reading phase)
- Full persistence: contract (with original blob + PDF blob), review, and clause-level results in PostgreSQL
- Frontend types rewritten for new backend API shape (polling response, completed review response)
- Frontend refactored to thin client: upload file → poll → fetch and display results
- Results survive page refresh (fetched from backend by contract ID)

## What We Are NOT Solving
- Contract list/history page (fast follow, not M3)
- Re-evaluation of an existing contract (1:1 contract-to-review for now)
- Contract deletion
- Playbook-based 132-check evaluation (deprecated, see deprecation-log.md)
- User authentication or multi-tenancy
- Full-text search over contract content
- Streaming evaluation results

## Actors & Triggers
- **User** uploads a contract file via the browser UI, optionally providing review instructions
- **Backend** receives the file, converts if needed, calls Anthropic, persists results
- **Frontend** polls for completion, fetches results, displays them

## Success Criteria
- User uploads a PDF, TXT, DOC, or DOCX file and sees evaluation results
- Refreshing the results page reloads results from the backend (no data loss)
- DOC/DOCX files are converted to PDF and the converted PDF is sent to Claude
- Frontend shows progress status while evaluation is in progress
- On failure, user sees a meaningful error message
- On non-contract input, user sees a clear "not a contract" message (not an error)
- Original uploaded file is preserved in the database alongside any converted PDF

## Interfaces

### Schemas

#### Contract (database)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK, auto-generated |
| name | str | Original filename |
| upload_type | str | `pdf`, `txt`, `doc`, `docx` |
| original_blob | bytes | Raw uploaded file |
| pdf_blob | bytes, nullable | PDF sent to Claude. For `pdf` uploads: copy of `original_blob`. For `doc`/`docx`: LibreOffice conversion. NULL only for `txt` uploads. |
| text | text, nullable | Plain text content. For `txt` uploads: file contents. NULL for others initially. |
| created_at | datetime | Auto-set |

Blob columns use deferred loading to avoid pulling bytes into memory on list/detail queries.

#### ContractReview (database)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK, auto-generated |
| contract_id | UUID | FK → contracts.id |
| status | str | `pending`, `reading`, `evaluating`, `completed`, `failed` |
| review_instructions | text, nullable | Optional user-provided instructions appended to the Claude prompt |
| overall_fairness | str, nullable | `fair`, `non-standard`, `dealbreaker`; set on completion. **NULL when completed = Claude determined input is not a contract** (see Completion States below) |
| summary | text, nullable | Set on completion. For non-contract input: contains the rejection reason (e.g. "This document does not appear to be a contract.") |
| call_to_action | JSON, nullable | Array of strings; set on completion |
| failure_message | text, nullable | Set only when status = `failed` (infrastructure/system errors) |
| created_at | datetime | Auto-set |
| completed_at | datetime, nullable | Set on completion or failure |

Previous fields `meta`, `priority_issues` are dropped (dead code). This is a destructive
migration — no production data exists.

#### Completion States

A review reaches a terminal state in one of three ways:

| State | status | overall_fairness | summary | failure_message | Meaning |
|-------|--------|-----------------|---------|-----------------|---------|
| **Success** | `completed` | `fair` / `non-standard` / `dealbreaker` | Evaluation summary | NULL | Normal evaluation with results and clauses |
| **Not a contract** | `completed` | NULL | Rejection reason from Claude | NULL | Claude successfully determined the input is not a contract. No clauses. |
| **Error** | `failed` | NULL | NULL | Error description | Infrastructure failure: conversion error, API timeout, invalid response, post-conversion PDF too large, etc. |

Frontend branching:
- `status === "completed" && overall_fairness !== null` → show results
- `status === "completed" && overall_fairness === null` → show "not a contract" message using `summary`
- `status === "failed"` → show error using `failure_message`

#### ReviewClause (database, replaces ReviewResult)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK, auto-generated |
| review_id | UUID | FK → contract_reviews.id |
| section_number | str | e.g. "3.1" |
| clause_type | str | e.g. "Termination", "Liability" |
| purpose | str | What the clause does |
| fairness | str | `fair`, `non-standard`, `dealbreaker` |
| market_standard | str | What market standard looks like |
| explanation | str | Why this rating was given |

### API Contracts

#### POST /api/contracts/upload
- **Input**: Multipart form data with `file` field and optional `instructions` text field
- **Validation**: Extension must be pdf/txt/doc/docx; max size 10MB
- **Post-conversion validation**: If converted PDF exceeds Claude's document block limit (~24MB raw), transition to `failed` with message
- **Response** (201):
  ```json
  { "contract_id": "uuid", "review_id": "uuid", "status": "pending" }
  ```
- **Errors**: 400 (invalid file type), 413 (file too large)

#### GET /api/reviews/{review_id}
- **Response** (in progress):
  ```json
  { "id": "uuid", "contract_id": "uuid", "status": "reading|evaluating|pending" }
  ```
- **Response** (completed — normal evaluation):
  ```json
  {
    "id": "uuid",
    "contract_id": "uuid",
    "status": "completed",
    "overall_fairness": "fair",
    "summary": "...",
    "call_to_action": ["..."],
    "clauses": [
      { "section_number": "3.1", "clause_type": "...", "fairness": "...", ... }
    ],
    "completed_at": "..."
  }
  ```
- **Response** (completed — not a contract):
  ```json
  {
    "id": "uuid",
    "contract_id": "uuid",
    "status": "completed",
    "overall_fairness": null,
    "summary": "This document does not appear to be a contract.",
    "call_to_action": null,
    "clauses": [],
    "completed_at": "..."
  }
  ```
- **Response** (failed):
  ```json
  { "id": "uuid", "status": "failed", "failure_message": "..." }
  ```

#### Polling Contract
- Frontend polls `GET /api/reviews/{review_id}` at 2s intervals
- Frontend timeout: 10 minutes (stop polling, show timeout error)
- Backend timeout: 90s for Anthropic API call; transitions to `failed` with message if exceeded

#### GET /api/contracts/{contract_id}/review
- **Response**: Same shape as `GET /api/reviews/{review_id}` — returns the single review for this contract (1:1 for M3)
- **Errors**: 404 (contract or review not found)
- **Purpose**: Frontend results page navigates by `contract_id`; this avoids needing to store `review_id` in the URL

#### GET /api/contracts (existing, keep)
#### GET /api/contracts/{id} (existing, keep)

#### Frontend URL Routing
- Results page: `/contract/[contract_id]` — fetches the review for this contract
- Upload redirects to `/contract/{contract_id}` after receiving the upload response
- 1:1 contract-to-review for M3; multi-review routing is a future problem

### System Boundaries
- **Anthropic API**: Claude receives PDF as document block or TXT as text; returns JSON matching EvalSuccess/EvalError shape. Backend timeout: 90s. Model and max_tokens configured via backend env vars (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_MAX_TOKENS`).
- **LibreOffice**: `libreoffice --headless --convert-to pdf` for DOC/DOCX conversion; system dependency
- **PostgreSQL**: Primary persistence for contracts, reviews, clauses

### Shared State
- **System prompt**: Moves to backend (Python). Frontend copy deleted. Backend is sole source of truth. JSON schema in the prompt will be generated from Pydantic models via `model_json_schema()`.
- **Frontend types**: Current Zod types (`EvalResponseSchema` with `error` discriminator) will be **rewritten** to match the new backend API shape. This is not an alignment task — it's a full replacement. New types will cover: upload response, polling response (pending/reading/evaluating), completed review with results, completed review with rejection, and failed review.

### Existing Code

#### Backend (destructive migration)
All existing tables will be dropped and recreated. No production data exists. Previous
`ReviewResult` model, `ReviewResultOut` schema, and playbook-based fields are removed
(see deprecation-log.md, commit `b0c239a` for history).

#### Backend (to be modified)
- `backend/models.py` — New schema: Contract (with blobs), ContractReview (with review_instructions, fairness fields, completion states), ReviewClause
- `backend/schemas.py` — New Pydantic schemas matching new models
- `backend/routers/contracts.py` — Add upload endpoint with file handling and post-conversion size validation
- `backend/routers/reviews.py` — Update to serve new schema shape with clauses; remove old create_review endpoint
- `backend/database.py` — No changes expected
- `backend/main.py` — No changes expected
- `backend/migrations/` — Fresh initial migration for all tables

#### Backend (new)
- `backend/services/evaluation.py` — Anthropic API call (includes review_instructions in prompt when provided), response parsing, DB persistence. Maps Claude's EvalError response to completed-with-null-fairness.
- `backend/services/conversion.py` — File type detection, LibreOffice conversion, post-conversion size check
- `backend/prompt.py` — System prompt (moved from frontend)

#### Frontend (to be modified — schemas first, then integration)
- `frontend/app/evaluate-contract/types.ts` — **Rewrite**: new types for upload response, polling states, completed review (with/without fairness), failed review
- `frontend/app/evaluate-contract/page.tsx` — Upload to backend instead of reading file locally; keep instructions field
- `frontend/app/evaluate-contract/validation.ts` — Update: accept pdf/doc/docx in addition to txt; keep 10MB limit
- `frontend/app/api/evaluate/route.ts` — Delete (backend handles evaluation now)
- `frontend/app/evaluate-contract/eval-result-context.tsx` — Replace with data fetched from backend
- `frontend/app/contract/[id]/page.tsx` — Fetch from backend API by contract_id instead of context; handle three completion states
- `frontend/prompt/` — Delete (backend is source of truth)

## Open Questions
- **LibreOffice in Docker**: Need to determine the right base image or installation approach for the Docker setup. Not a blocker for the spec but needs resolution during planning.
- **Blob storage**: PostgreSQL blob storage is fine for dev. Production should use AWS S3 or GCS with references in PostgreSQL. TODO: add a storage abstraction layer so the switch is config-driven across environments.
- **Claude PDF comprehension parity**: The system prompt was tuned for plain text input. Verify that Claude's JSON output quality and schema compliance are equivalent when receiving a PDF document block vs. plain text. May need prompt adjustments.
- **Text extraction for search**: Storing extracted text alongside blobs would enable future search. Deferred — not M3 scope.
- **Background task durability**: Using FastAPI `BackgroundTasks` for M3 (in-process, lost on restart). TODO: migrate to a proper task queue (Celery/ARQ) if evaluation reliability becomes an issue.
