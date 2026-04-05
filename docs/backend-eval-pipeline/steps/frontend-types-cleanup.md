# Step 11: frontend-types-cleanup

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Sequential (after step 9)

## What This Step Delivers

Complete rewrite of frontend Zod types for new backend API shape. Updated file validation
(PDF/DOC/DOCX, 10MB). Deletion of old evaluation route, prompt files, and obsolete tests.
After this step, the frontend compiles and existing display components still work.

## Done When

- New Zod schemas: `UploadResponseSchema`, `ReviewPollingSchema`, `ReviewCompletedSchema`, `ReviewFailedSchema`, `ReviewResponseSchema`
- Old `EvalResponseSchema`, `EvalSuccessSchema`, `EvalErrorSchema` removed
- `validation.ts` accepts `.pdf`, `.doc`, `.docx`, `.txt` and 10MB limit
- `frontend/app/api/evaluate/route.ts` deleted
- `frontend/prompt/` directory deleted
- Obsolete tests deleted (`api-evaluate.test.ts`, `prompt.test.ts`)
- `npm run build` succeeds with zero type errors
- `npm test` passes for all remaining tests

## Cycles

### new-zod-types

**Test** — write these tests and confirm they fail:
- **test_upload_response_schema**: `UploadResponseSchema.parse(...)` succeeds with valid data, fails with missing fields.
- **test_review_polling_schema**: Parses pending/reading/evaluating states.
- **test_review_completed_with_fairness**: Parses completed review with clauses.
- **test_review_completed_null_fairness**: Parses completed review with `overall_fairness: null` and empty clauses.
- **test_review_failed_schema**: Parses failed review with `failure_message`.
- **test_discriminated_union**: `ReviewResponseSchema` correctly dispatches on `status`.

**Code** — Rewrite `frontend/app/evaluate-contract/types.ts`:
- Keep `FairnessRatingSchema` (used by display components)
- `ReviewClauseSchema`: `id`, `section_number`, `clause_type`, `purpose`, `fairness`, `market_standard`, `explanation`
- `UploadResponseSchema`: `contract_id`, `review_id`, `status` (literal "pending")
- `ReviewPollingSchema`: `id`, `contract_id`, `status` (enum: pending/reading/evaluating)
- `ReviewCompletedSchema`: `id`, `contract_id`, `status` (literal "completed"), `overall_fairness` (nullable), `summary`, `call_to_action`, `clauses`, `completed_at`
- `ReviewFailedSchema`: `id`, `status` (literal "failed"), `failure_message`
- `ReviewResponseSchema`: discriminated union on `status`
- Export all types

**Refactor** — none

**Commit**: `Rewrite frontend Zod types for backend API`

---

### update-validation

**Test** — write these tests and confirm they fail:
- **test_pdf_valid**: `validateFileExtension("contract.pdf")` → true
- **test_doc_valid**: `validateFileExtension("contract.doc")` → true
- **test_docx_valid**: `validateFileExtension("contract.docx")` → true
- **test_txt_still_valid**: `validateFileExtension("contract.txt")` → true
- **test_png_invalid**: `validateFileExtension("image.png")` → false
- **test_10mb_limit**: `validateFileSize(10 * 1024 * 1024)` → true, `validateFileSize(10 * 1024 * 1024 + 1)` → false

**Code** — Update `validation.ts`:
- `ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.doc', '.docx']`
- `MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024`

**Refactor** — none

**Commit**: `Accept PDF/DOC/DOCX, increase size limit to 10MB`

---

### delete-old-code

**Test** — No new tests. Verify build + existing tests pass after deletion.

**Code** — Delete:
- `frontend/app/api/evaluate/route.ts`
- `frontend/prompt/system-prompt.ts`
- `frontend/prompt/index.ts`
- `frontend/__tests__/api-evaluate.test.ts`
- `frontend/__tests__/prompt.test.ts`

Remove imports of deleted modules from other files.

**Refactor** — none

**Commit**: `Delete old evaluation route, prompt, and obsolete tests`

---

## Verification

```bash
cd frontend

# Build must succeed with zero errors:
npm run build
# Expected: Compiled successfully

# All tests must pass:
npm test
# Expected: all passing, no failures from deleted imports or missing types

# Verify deleted files are gone:
ls app/api/evaluate/route.ts 2>/dev/null && echo "FAIL: route.ts still exists" || echo "OK: route.ts deleted"
ls prompt/system-prompt.ts 2>/dev/null && echo "FAIL: prompt still exists" || echo "OK: prompt deleted"
```
