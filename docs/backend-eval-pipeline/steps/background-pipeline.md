# Step 9: background-pipeline

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Sequential (after steps 5, 7, 8)

## What This Step Delivers

Wires `BackgroundTasks` to the upload endpoint. After upload, a background task runs:
conversion (if needed) → evaluation → persist results. Status progresses through
reading → evaluating → completed/failed. This is the full backend E2E integration point.

## Done When

- Upload endpoint kicks off background task
- Status transitions: pending → reading → evaluating → completed (or failed at any stage)
- TXT: skips reading, goes straight to evaluating
- DOC/DOCX: reading status while LibreOffice converts
- Conversion errors → failed with message
- Evaluation errors → failed with message
- Full round-trip works: upload → poll → see completed results

## Cycles

### background-task-function

**Test** — write these tests and confirm they fail:
- **test_background_task_completes**: Create contract + review in DB. Mock `process_upload` to return ConversionResult, mock `run_evaluation` to set completed. Call `evaluate_contract_task(review_id, contract_id)`. Assert review status is `completed`.
- **test_background_task_conversion_failure**: Mock `process_upload` to raise `ValueError`. Call task. Assert review `status="failed"`, `failure_message` contains error.
- **test_background_task_sets_reading_for_docx**: Create contract with `upload_type="docx"`. Call task. Assert status was set to `reading` before conversion. (Inspect via a side-effect mock.)

**Code** — Create `evaluate_contract_task(review_id, contract_id)` (in `services/evaluation.py` or new `backend/tasks.py`):
1. Open new DB session
2. Load contract and review
3. If `upload_type` in `["doc", "docx"]`: set `status="reading"`, flush, run conversion, update contract blobs
4. Set `status="evaluating"`, flush
5. Call `run_evaluation(review_id, contract, db)`
6. On any exception: set `status="failed"`, `failure_message`, commit

**Refactor** — none

**Commit**: `Add background evaluation task with status transitions`

---

### wire-to-upload-endpoint

**Test** — write these tests and confirm they fail:
- **test_upload_triggers_background**: POST a `.txt` file. Wait briefly (or mock). Query review. Assert status has progressed past `pending`.
- **test_upload_and_poll_completed**: POST `.txt`. Poll `GET /api/reviews/{review_id}` until terminal. Assert `status="completed"` with results. · setup: mock Anthropic, real DB

**Code** — Add `background_tasks: BackgroundTasks` parameter to `upload_contract`. After commit, call `background_tasks.add_task(evaluate_contract_task, review.id, contract.id)`.

**Refactor** — none

**Commit**: `Wire background task to upload endpoint`

---

## Verification

```bash
cd backend && make reset-db && make dev

# === Test 1: TXT upload (should skip reading, go to evaluating → completed) ===
UPLOAD=$(curl -s -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@../docs/gc-ai-takehome/test-contract.txt" \
  -F "instructions=Focus on liability clauses")
echo "$UPLOAD" | python -m json.tool
REVIEW_ID=$(echo "$UPLOAD" | python -c "import sys,json; print(json.load(sys.stdin)['review_id'])")

# Poll every 2s:
for i in $(seq 1 30); do
  RESULT=$(curl -s http://localhost:8000/api/reviews/$REVIEW_ID)
  STATUS=$(echo "$RESULT" | python -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Poll $i: status=$STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo "$RESULT" | python -m json.tool
    break
  fi
  sleep 2
done

# Expected: status transitions pending → evaluating → completed
# Completed response should have: overall_fairness, summary, call_to_action, clauses[]

# === Test 2: Non-contract input ===
echo "Chocolate chip cookie recipe: mix flour, sugar, butter" > /tmp/recipe.txt
UPLOAD2=$(curl -s -X POST http://localhost:8000/api/contracts/upload \
  -F "file=@/tmp/recipe.txt")
REVIEW_ID2=$(echo "$UPLOAD2" | python -c "import sys,json; print(json.load(sys.stdin)['review_id'])")

for i in $(seq 1 15); do
  RESULT2=$(curl -s http://localhost:8000/api/reviews/$REVIEW_ID2)
  STATUS2=$(echo "$RESULT2" | python -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Poll $i: status=$STATUS2"
  if [ "$STATUS2" = "completed" ] || [ "$STATUS2" = "failed" ]; then
    echo "$RESULT2" | python -m json.tool
    break
  fi
  sleep 2
done

# Expected: status=completed, overall_fairness=null, summary contains rejection reason

# === Test 3: DOCX upload (if LibreOffice installed) ===
# curl -s -X POST http://localhost:8000/api/contracts/upload -F "file=@contract.docx"
# Poll: expect reading → evaluating → completed
```
