# Step 8: upload-endpoint

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B2 (parallel)

## What This Step Delivers

`POST /api/contracts/upload` that accepts multipart file + optional instructions, validates
the file, persists the contract with blobs, creates a pending review, and returns IDs. No
background task yet — that's step 9. Updated contract list/detail endpoints for new schema.

## Done When

- POST with valid file returns 201 with `{contract_id, review_id, status: "pending"}`
- POST with invalid extension returns 400
- POST with file > 10MB returns 413
- Contract persisted with correct blobs (via `process_upload`)
- ContractReview created with `status="pending"` and `review_instructions` if provided
- `GET /api/contracts/` returns list without blob fields
- `GET /api/contracts/{id}` returns detail with text but no blobs

## Cycles

### upload-happy-path

**Test** — write these tests and confirm they fail:
- **test_upload_txt_returns_201**: POST multipart with a `.txt` file. Assert 201, response has `contract_id`, `review_id`, `status="pending"`.
- **test_upload_stores_contract**: After upload, GET `/api/contracts/{contract_id}`. Assert `name` matches filename, `upload_type="txt"`.
- **test_upload_with_instructions**: POST with file + `instructions=Focus on IP`. Query review from DB. Assert `review_instructions == "Focus on IP"`.

**Code** — Add to `backend/routers/contracts.py`:
```python
@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_contract(
    file: UploadFile,
    instructions: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    result = process_upload(file.filename, file_bytes)
    contract = Contract(
        name=file.filename,
        upload_type=result.upload_type,
        original_blob=result.original_blob,
        pdf_blob=result.pdf_blob,
        text=result.text,
    )
    db.add(contract)
    await db.flush()
    review = ContractReview(contract_id=contract.id, status="pending", review_instructions=instructions)
    db.add(review)
    await db.commit()
    return UploadResponse(contract_id=contract.id, review_id=review.id, status="pending")
```

**Refactor** — none

**Commit**: `Add POST /api/contracts/upload endpoint`

---

### upload-validation

**Test** — write these tests and confirm they fail:
- **test_upload_rejects_png**: POST with `.png`. Assert 400, body contains "unsupported".
- **test_upload_rejects_oversized**: POST with > 10MB file. Assert 413.
- **test_upload_accepts_pdf**: POST with `.pdf`. Assert 201.

**Code** — Add validation before `process_upload`: check file size, catch `ValueError` from `process_upload` and return 400. Add 413 response for oversized files.

**Refactor** — Extract `MAX_UPLOAD_SIZE = 10 * 1024 * 1024`.

**Commit**: `Add file validation to upload endpoint`

---

### update-contract-list-detail

**Test** — write these tests and confirm they fail:
- **test_list_contracts_no_blobs**: Upload a contract. GET `/api/contracts/`. Assert response has `name`, `upload_type` but no `original_blob` or `pdf_blob` keys.
- **test_get_contract_detail**: GET `/api/contracts/{id}`. Assert has `text` field.
- **test_get_contract_not_found**: GET with nonexistent ID. Assert 404.

**Code** — Update existing routes in `contracts.py` to use new `ContractOut` and `ContractDetailOut` schemas. Ensure deferred blob columns aren't loaded by the query.

**Refactor** — none

**Commit**: `Update contract list/detail for new schema`

---

## Verification

```bash
cd backend && make dev

# Upload TXT:
curl -s -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@../docs/gc-ai-takehome/test-contract.txt" \
  -F "instructions=Focus on liability" | python -m json.tool
# Expected: {"contract_id": "...", "review_id": "...", "status": "pending"}

# Invalid extension:
echo "not a contract" > /tmp/test.png
curl -s -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@/tmp/test.png"
# Expected: 400, {"detail": "...unsupported..."}

# List contracts:
curl -s http://localhost:8000/api/contracts/ | python -m json.tool
# Expected: array with contract, no blob fields

# Detail:
curl -s http://localhost:8000/api/contracts/{contract_id} | python -m json.tool
# Expected: contract with text field
```
