# Step 6: anthropic-client

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Sequential (after Batch 2)

## What This Step Delivers

Anthropic API message building and response parsing. Builds the correct message format for PDF
(document block) and TXT (text). Parses Claude's response into success, not-a-contract, or
parse error. All tested with mocked Anthropic client — no real API calls.

## Done When

- `build_messages(pdf_blob, text, instructions)` produces correct Anthropic message params
- PDF: message contains `document` content block with base64-encoded bytes
- TXT: message contains plain text content
- `parse_response(raw_text)` returns `("success", data)`, `("not_a_contract", data)`, or `("parse_error", data)`
- Markdown fence stripping works
- `max_tokens` stop reason detected

## Cycles

### build-message-pdf

**Test** — write these tests and confirm they fail:
- **test_build_message_pdf**: Call `build_messages(pdf_blob=b"fake", text=None, instructions=None)`. Assert `messages[0]["content"]` contains a dict with `type: "document"`, `source.type: "base64"`, `source.media_type: "application/pdf"`.
- **test_build_message_pdf_with_instructions**: Same with `instructions="Focus on IP"`. Assert `system` contains "Additional instructions".

**Code** — Create `backend/services/evaluation.py`. Implement `build_messages(pdf_blob, text, instructions) -> dict`. For PDF: base64-encode blob, create document content block. Set system via `build_system_prompt(instructions)`.

**Refactor** — none

**Commit**: `Build Anthropic message for PDF documents`

---

### build-message-text

**Test** — write these tests and confirm they fail:
- **test_build_message_text**: Call `build_messages(pdf_blob=None, text="Contract text")`. Assert `messages[0]["content"]` is the plain text string.
- **test_build_message_requires_one**: Call with both `None`. Assert raises `ValueError`.

**Code** — Add text branch. If `pdf_blob is None`, use `text` as plain string content.

**Refactor** — none

**Commit**: `Build Anthropic message for text documents`

---

### parse-success-response

**Test** — write these tests and confirm they fail:
- **test_parse_success**: Valid EvalSuccess JSON → returns `("success", data)` with all fields.
- **test_parse_strips_fences**: JSON wrapped in ` ```json ... ``` ` → parses correctly.

**Code** — Implement `parse_response(raw_text: str) -> tuple[str, dict]`. Strip fences, parse JSON, validate against `EvalSuccessResponse` Pydantic model.

**Refactor** — none

**Commit**: `Parse EvalSuccess from Claude response`

---

### parse-error-and-invalid

**Test** — write these tests and confirm they fail:
- **test_parse_eval_error**: `{"error": true, "reason": "Not a contract"}` → `("not_a_contract", {"reason": "..."})`.
- **test_parse_invalid_json**: Malformed text → `("parse_error", {"message": "..."})`.
- **test_parse_wrong_schema**: Valid JSON but wrong shape → `("parse_error", {"message": "..."})`.

**Code** — Try EvalSuccess first, then EvalError. If neither validates, return `parse_error`.

**Refactor** — none

**Commit**: `Parse EvalError and handle invalid responses`

---

## Verification

```python
# Run in Python REPL from backend/:
from services.evaluation import build_messages
import json

# PDF message:
msg = build_messages(pdf_blob=b"fake-pdf-bytes", text=None, instructions=None)
content = msg["messages"][0]["content"]
assert isinstance(content, list)
doc_block = content[0]
assert doc_block["type"] == "document"
assert doc_block["source"]["type"] == "base64"
assert doc_block["source"]["media_type"] == "application/pdf"
print(f"PDF message: document block with {len(doc_block['source']['data'])} base64 chars")

# Text message:
msg2 = build_messages(pdf_blob=None, text="Contract text here", instructions=None)
content2 = msg2["messages"][0]["content"]
assert content2 == "Contract text here"
print(f"Text message: plain string content")

# System prompt present:
assert "senior in-house commercial lawyer" in msg["system"]
print("System prompt: OK")

# Parse response:
from services.evaluation import parse_response
kind, data = parse_response('{"error": null, "overall_fairness": "fair", "summary": "test", "call_to_action": [], "clauses": []}')
assert kind == "success"
print(f"Parse success: OK")

kind2, data2 = parse_response('{"error": true, "reason": "Not a contract"}')
assert kind2 == "not_a_contract"
print(f"Parse not-a-contract: OK")
```
