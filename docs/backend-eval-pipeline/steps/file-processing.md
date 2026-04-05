# Step 4: file-processing

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B1 (parallel with step 1)

## What This Step Delivers

Conversion service handling TXT and PDF files (no LibreOffice dependency). `process_upload()`
returns a `ConversionResult` dataclass with the correct blob/text population for each type.
Invalid extensions rejected. DOC/DOCX support is stubbed (raises NotImplementedError) — step 5
adds LibreOffice.

## Done When

- `process_upload("file.txt", bytes)` returns `ConversionResult` with `text` set, `pdf_blob=None`
- `process_upload("file.pdf", bytes)` returns `ConversionResult` with `pdf_blob` = copy of input, `text=None`
- `process_upload("file.png", bytes)` raises `ValueError`
- `process_upload("file.docx", bytes)` raises `NotImplementedError` (placeholder for step 5)

## Cycles

### conversion-result-and-txt

**Test** — write these tests and confirm they fail:
- **test_process_txt**: Call `process_upload("contract.txt", b"Hello world")`. Assert `upload_type="txt"`, `text="Hello world"`, `pdf_blob is None`, `original_blob=b"Hello world"`.
- **test_process_txt_utf8**: Call with `"résumé clause §3".encode("utf-8")`. Assert text decodes correctly.

**Code** — Create `backend/services/__init__.py` (empty) and `backend/services/conversion.py`. Define `ConversionResult` dataclass. Implement `process_upload(filename, file_bytes)` for `.txt`: decode UTF-8, return result.

**Refactor** — none

**Commit**: `Add conversion service with TXT processing`

---

### pdf-passthrough

**Test** — write these tests and confirm they fail:
- **test_process_pdf**: Call `process_upload("contract.pdf", b"fake-pdf")`. Assert `upload_type="pdf"`, `pdf_blob=b"fake-pdf"`, `text is None`, `original_blob=b"fake-pdf"`.

**Code** — Add `.pdf` branch: copy bytes into both `original_blob` and `pdf_blob`.

**Refactor** — none

**Commit**: `Add PDF passthrough with blob copy`

---

### extension-validation

**Test** — write these tests and confirm they fail:
- **test_reject_png**: `process_upload("image.png", b"x")` raises `ValueError` with "unsupported".
- **test_reject_no_extension**: `process_upload("noext", b"x")` raises `ValueError`.
- **test_doc_not_implemented**: `process_upload("file.doc", b"x")` raises `NotImplementedError`.
- **test_docx_not_implemented**: `process_upload("file.docx", b"x")` raises `NotImplementedError`.

**Code** — Add extension extraction + validation. `.doc`/`.docx` raise `NotImplementedError("LibreOffice conversion not yet implemented")`.

**Refactor** — Extract `get_upload_type(filename) -> str` helper.

**Commit**: `Validate file extensions, stub DOC/DOCX`

---

## Verification

```python
# Run in Python REPL or test script:
from services.conversion import process_upload

# TXT:
r = process_upload("test.txt", b"Section 1. The vendor shall...")
assert r.upload_type == "txt"
assert r.text == "Section 1. The vendor shall..."
assert r.pdf_blob is None
print("TXT: OK")

# PDF:
with open("test-contract.pdf", "rb") as f:
    pdf_bytes = f.read()
r = process_upload("test-contract.pdf", pdf_bytes)
assert r.upload_type == "pdf"
assert r.pdf_blob == pdf_bytes
assert r.text is None
print(f"PDF: OK, pdf_blob={len(r.pdf_blob)} bytes")
```
