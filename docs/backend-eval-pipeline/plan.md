# Plan: Backend-First Contract Evaluation Pipeline (M3)

> Spec: [spec.md](spec.md)

## File Map

```
Create: backend/services/__init__.py               — Package init
Create: backend/services/conversion.py             — File type detection, LibreOffice DOC/DOCX→PDF
Create: backend/services/evaluation.py             — Anthropic API call, response parsing, DB persistence
Create: backend/prompt.py                          — System prompt (ported from frontend TS)
Create: backend/migrations/versions/001_initial.py — Fresh initial migration
Modify: backend/models.py                          — Contract (blobs), ContractReview (fairness), ReviewClause
Modify: backend/schemas.py                         — Pydantic schemas for new models + API responses
Modify: backend/routers/contracts.py               — Upload endpoint (multipart), keep list/detail
Modify: backend/routers/reviews.py                 — GET review with clauses, GET by contract_id
Modify: backend/pyproject.toml                     — Add anthropic, python-multipart, python-docx deps
Modify: backend/Makefile                           — Add reset-db target
Modify: frontend/app/evaluate-contract/types.ts    — Full rewrite: new API response types
Modify: frontend/app/evaluate-contract/validation.ts — Accept pdf/doc/docx, bump to 10MB
Modify: frontend/app/evaluate-contract/page.tsx    — Upload to backend, polling, instructions
Modify: frontend/app/contract/[id]/page.tsx        — Fetch from backend, three completion states
Delete: frontend/app/evaluate-contract/eval-result-context.tsx — Replaced by backend fetch
Delete: frontend/app/api/evaluate/route.ts         — Backend handles evaluation now
Delete: frontend/prompt/system-prompt.ts           — Backend is source of truth
Delete: frontend/prompt/index.ts                   — No longer needed
Test:   backend/tests/test_models.py               — Model round-trip tests
Test:   backend/tests/test_schemas.py              — Pydantic serialization tests
Test:   backend/tests/test_contracts.py            — Rewrite: upload endpoint, file validation
Test:   backend/tests/test_reviews.py              — Rewrite: review polling, completion states
Test:   backend/tests/test_conversion.py           — Conversion service unit tests
Test:   backend/tests/test_evaluation.py           — Evaluation service unit tests
Test:   backend/tests/test_prompt.py               — Prompt generation tests
Modify: frontend/__tests__/types.test.ts           — Rewrite for new types
Modify: frontend/__tests__/validation.test.ts      — Update for new extensions/size
Modify: frontend/__tests__/evaluate-contract-page.test.tsx — Rewrite for upload + polling flow
Modify: frontend/__tests__/contract-results-page.test.tsx  — Rewrite for backend fetch + 3 states
```

## Execution Strategy

One Claude orchestrating, parallel agents at clean file boundaries. No worktrees needed —
parallel steps touch non-overlapping files.

```
Batch 1 (parallel):   1-backend-models + 4-file-processing
Step 2 (sequential):  2-pydantic-and-migration
Batch 2 (parallel):   3-system-prompt + 5-doc-docx-conversion + 8-upload-endpoint + 10-review-endpoints
Step 6 (sequential):  6-anthropic-client
Step 7 (sequential):  7-evaluation-persistence
Step 9 (sequential):  9-background-pipeline
Step 11 (sequential): 11-frontend-types-cleanup
Batch 3 (parallel):   12-upload-page + 13-results-page
```

9 serial checkpoints, 3 parallel batches. Critical path: 9 steps instead of 13.

**Human checkpoints** — batched at natural boundaries:
- After Batch 2: review all backend foundation (models, schemas, prompt, conversion, endpoints)
- After Step 9: review full backend pipeline E2E
- After Batch 3: review full frontend integration E2E

---

## Status Dashboard

| #  | Step                                                                 | Blocks              | Batch | Auto Tests | Verify | Simplify | Review | Human |
| -- | -------------------------------------------------------------------- | -------------------- | ----- | :--------: | :----: | :------: | :----: | :---: |
| 1  | [backend-models](steps/backend-models.md)                            | 2                    | B1    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 4  | [file-processing](steps/file-processing.md)                          | 5, 8                 | B1    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 2  | [pydantic-and-migration](steps/pydantic-and-migration.md)            | 3, 8, 10             | seq   |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 3  | [system-prompt](steps/system-prompt.md)                              | 6                    | B2    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 5  | [doc-docx-conversion](steps/doc-docx-conversion.md)                  | 9                    | B2    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 8  | [upload-endpoint](steps/upload-endpoint.md)                          | 9                    | B2    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 10 | [review-endpoints](steps/review-endpoints.md)                        | 11                   | B2    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 6  | [anthropic-client](steps/anthropic-client.md)                        | 7                    | seq   |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 7  | [evaluation-persistence](steps/evaluation-persistence.md)            | 9                    | seq   |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 9  | [background-pipeline](steps/background-pipeline.md)                  | 11                   | seq   |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 11 | [frontend-types-cleanup](steps/frontend-types-cleanup.md)            | 12, 13               | seq   |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 12 | [upload-page](steps/upload-page.md)                                  | —                    | B3    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 13 | [results-page](steps/results-page.md)                                | —                    | B3    |     ✅     |   ✅   |    ✅    |   ✅   |  ✅   |
| 14 | playbook-parser                                                      | —                    | seq   |     ✅     |   ⬜   |    ⬜    |   ⬜   |  ⬜   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow per step:** Auto Tests → Verify → Simplify → Review → Human (batched)

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: LLM-driven verification against live system (NEVER skipped unless ➖)
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Human**: developer sign-off + `/learn-from-mistakes` (batched at boundaries)

---

## Verification Strategy

> "Your job is to deliver code you have proven to work."
> — [Simon Willison](https://simonwillison.net/2025/Dec/18/code-proven-to-work/)

Every step must produce **evidence** that it works — not confidence, not "tests pass", but
observable proof: command output, database state, browser behavior. Automated tests and manual
verification are complementary; one does not substitute for the other. ➖ (N/A) is only valid
after exhausting all verification paths (DB inspection, file output, compiler checks, etc.).

| Step | Verification method | What to check |
|------|-------------------|---------------|
| 1. backend-models | DB round-trip via test DB | Insert contract + review + clauses, query back, assert all fields |
| 2. pydantic-and-migration | `alembic upgrade head` + `psql \dt` + `\d` | Tables exist, columns match spec schema exactly |
| 3. system-prompt | Print prompt output, diff key sections | Prompt contains analysis rules, JSON schemas match Pydantic models |
| 4. file-processing | Process real .txt and .pdf files | Print ConversionResult fields, assert correct blob/text population |
| 5. doc-docx-conversion | Convert real .docx → write PDF to disk | Open output PDF, verify content readable and matches source |
| 6. anthropic-client | Print built message structure | Verify document block has correct base64 encoding, media type, system prompt |
| 7. evaluation-persistence | Run against test DB, inspect rows | Print review row + clause rows after mock evaluation completes |
| 8. upload-endpoint | `curl -F file=@test.txt ...` | 201 response, contract in DB via `curl GET`, review in DB |
| 9. background-pipeline | `curl` upload → poll → completed | Full E2E: upload, status transitions, completed with clauses |
| 10. review-endpoints | `curl` GET endpoints | Correct response shapes for all states, 404 for missing |
| 11. frontend-types-cleanup | `npm run build` + `npm test` | Zero type errors, all remaining tests pass, deleted files gone |
| 12. upload-page | Browser: upload file, observe flow | File sent to backend, status shown, redirect on completion |
| 13. results-page | Browser: view results, refresh page | Results persist across refresh, 3 states render correctly |

---

## Branching Strategy

**Single feature branch** (`m3-backend-eval-pipeline`). Linear commit history with TDD
red-green-refactor commits within each step. Parallel agents commit to the same branch
since they touch non-overlapping files.

---

## Steps

### 1. backend-models (Batch 1)

SQLAlchemy models: Contract (with `original_blob`, `pdf_blob`, `upload_type`, `text`),
ContractReview (with `review_instructions`, `overall_fairness`, `call_to_action`,
`failure_message`, completion states), ReviewClause (replaces ReviewResult). Done when
all model fields round-trip through SQLite test DB.

**Verify**: Insert a contract, review, and clause via test DB. Query back. Assert all fields.
[→ Detailed plan](steps/backend-models.md)

### 4. file-processing (Batch 1, parallel with 1)

Conversion service for TXT and PDF only (no LibreOffice dependency). `process_upload()` returns
`ConversionResult` with correct blob/text population. PDF uploads copy into `pdf_blob`. TXT
uploads set `text`, `pdf_blob=None`. Invalid extensions rejected.

**Verify**: Call `process_upload` with a real `.txt` file and a real `.pdf` file. Print
ConversionResult fields. Assert `pdf_blob` populated for PDF, `text` populated for TXT.
[→ Detailed plan](steps/file-processing.md)

### 2. pydantic-and-migration (after Batch 1)

Pydantic schemas matching new models + API response shapes. Fresh Alembic migration (destructive
reset). Done when schemas serialize all completion states and `alembic upgrade head` creates
correct tables.

**Verify**: Run `alembic upgrade head` against real PostgreSQL. Connect via psql, run `\dt` to
list tables. Run `\d contracts`, `\d contract_reviews`, `\d review_clauses` to inspect columns.
Assert tables and columns match spec.
[→ Detailed plan](steps/pydantic-and-migration.md)

### 3. system-prompt (Batch 2)

Port system prompt from TypeScript to Python. JSON schema generated from Pydantic models via
`model_json_schema()`. Injection point for `review_instructions`.

**Verify**: ➖ N/A — No external surface. Verified through unit tests only.
[→ Detailed plan](steps/system-prompt.md)

### 5. doc-docx-conversion (Batch 2, parallel)

Extend conversion service for DOC/DOCX via LibreOffice headless. Post-conversion size check
(>24MB rejects). Done when a real `.docx` file converts to a valid PDF.

**Verify**: Call `process_upload` with a real `.docx` file. Write the resulting `pdf_blob` to
disk. Open the PDF and confirm content is readable and matches the source document.
[→ Detailed plan](steps/doc-docx-conversion.md)

### 8. upload-endpoint (Batch 2, parallel)

`POST /api/contracts/upload` accepts multipart file + optional instructions. Validates extension
and size. Creates contract + pending review. Returns `{contract_id, review_id, status}`.
No background task yet (step 9).

**Verify**:
```bash
curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@test-contract.txt" \
  -F "instructions=Focus on liability"
# Assert: 201, {contract_id, review_id, status: "pending"}

curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@image.png"
# Assert: 400, invalid file type

curl http://localhost:8000/api/contracts/
# Assert: contract appears in list with name and upload_type
```
[→ Detailed plan](steps/upload-endpoint.md)

### 10. review-endpoints (Batch 2, parallel)

`GET /api/reviews/{review_id}` returns correct shape for all states. `GET /api/contracts/{contract_id}/review` returns the single review for a contract. Updated contract list/detail endpoints for new schema.

**Verify**:
```bash
# After uploading a contract (step 8):
curl http://localhost:8000/api/reviews/{review_id}
# Assert: pending review shape

# Manually set review to completed in DB, then:
curl http://localhost:8000/api/reviews/{review_id}
# Assert: completed shape with clauses

curl http://localhost:8000/api/contracts/{contract_id}/review
# Assert: same review returned
```
[→ Detailed plan](steps/review-endpoints.md)

### 6. anthropic-client (after Batch 2)

Build Anthropic API messages for PDF (document block) and TXT (text). Parse Claude's response
into success, not-a-contract, or error. Strip markdown fences. Handle `max_tokens` stop reason.

**Verify**: ➖ N/A — All testing via mocked Anthropic client. Real API call verified in step 9.
[→ Detailed plan](steps/anthropic-client.md)

### 7. evaluation-persistence (after step 6)

`run_evaluation()` orchestrates: set status → call Anthropic → parse → persist to DB. Covers
all three completion states. Status transitions are atomic.

**Verify**: ➖ N/A — DB persistence tested via mocked API client. Full E2E in step 9.
[→ Detailed plan](steps/evaluation-persistence.md)

### 9. background-pipeline (after steps 5, 7, 8)

Wire `BackgroundTasks`: upload endpoint kicks off conversion → evaluation as background task.
Status progresses through reading → evaluating → completed/failed. This is the full backend
E2E integration point.

**Verify** (full E2E):
```bash
# Upload a real contract:
curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@test-contract.txt" \
  -F "instructions=Focus on liability"
# Save review_id from response

# Poll until completed:
watch -n 2 'curl -s http://localhost:8000/api/reviews/{review_id} | python -m json.tool'
# Assert: status transitions pending → evaluating → completed
# Assert: completed response has overall_fairness, summary, clauses

# Upload a non-contract:
curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@recipe.txt"
# Poll: assert completed with overall_fairness=null, summary contains rejection reason

# Upload a .docx (if LibreOffice available):
curl -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@contract.docx"
# Poll: assert reading → evaluating → completed
```
[→ Detailed plan](steps/background-pipeline.md)

### 11. frontend-types-cleanup (after steps 9, 10)

Rewrite Zod types for backend API shape. Update validation (pdf/doc/docx, 10MB). Delete old
evaluation route, prompt files, and their tests.

**Verify**:
```bash
cd frontend && npm run build
# Assert: zero type errors, builds successfully

cd frontend && npm test
# Assert: all remaining tests pass (deleted tests removed)
```
[→ Detailed plan](steps/frontend-types-cleanup.md)

### 12. upload-page (Batch 3)

Rewrite upload page: multipart POST to backend, poll for status, show progress, redirect on
completion. Remove eval-result-context dependency.

**Verify** (browser):
1. Open `http://localhost:3000/evaluate-contract`
2. Upload a `.txt` contract file with instructions
3. Assert: loading state appears with status updates
4. Assert: redirects to `/contract/{contract_id}` on completion
5. Upload an invalid file type → assert error message
[→ Detailed plan](steps/upload-page.md)

### 13. results-page (Batch 3, parallel with 12)

Rewrite results page: fetch from backend by contract_id, handle success/rejection/failed states.
Remove eval-result-context. Results survive page refresh.

**Verify** (browser):
1. Navigate to `/contract/{contract_id}` (from a completed evaluation)
2. Assert: results displayed with clauses, fairness badges
3. Refresh the page → assert results still displayed (no data loss)
4. Navigate to a contract with non-contract input → assert "not a contract" message
5. Navigate to a nonexistent contract → assert "not found" message
[→ Detailed plan](steps/results-page.md)

---

## Human Checkpoints

Human review, `/learn-from-mistakes`, and `/pr-interactive-walkthrough` are batched at
three natural boundaries:

### Checkpoint 1: Backend Foundation (after Batch 2)
Steps 1, 4, 2, 3, 5, 8, 10 — models, schemas, prompt, conversion, endpoints
- Review: all backend code committed so far
- Walkthrough: commit range from start of M3 branch to end of Batch 2

### Checkpoint 2: Backend E2E (after Step 9)
Steps 6, 7, 9 — Anthropic integration, persistence, background pipeline
- Review: full backend pipeline
- Walkthrough: commit range from Batch 2 to step 9
- Verify: live curl tests against running backend

### Checkpoint 3: Frontend Complete (after Batch 3)
Steps 11, 12, 13 — types, upload page, results page
- Review: all frontend changes
- Walkthrough: commit range from step 9 to end
- Verify: full browser E2E test
- `/learn-from-mistakes` for the entire M3
