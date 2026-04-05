# Step 5: doc-docx-conversion

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md) · Batch: B2 (parallel)

## What This Step Delivers

LibreOffice-based conversion for DOC and DOCX files. Extends step 4's `process_upload()` to
handle `.doc` and `.docx` by converting to PDF via `libreoffice --headless`. Includes
post-conversion size validation (>24MB rejects). After this step, all four file types are
supported.

## Done When

- `process_upload("file.docx", bytes)` returns `ConversionResult` with `pdf_blob` from LibreOffice
- `process_upload("file.doc", bytes)` same behavior
- Post-conversion PDF > 24MB raises `ValueError`
- LibreOffice errors raise `RuntimeError` with descriptive message

## Cycles

### docx-conversion

**Test** — write these tests and confirm they fail:
- **test_process_docx**: Call `process_upload("contract.docx", b"fake-docx")` with LibreOffice subprocess mocked to write a fake PDF. Assert `upload_type="docx"`, `pdf_blob` is the mock output, `text is None`.
- **test_process_doc**: Same for `.doc`.
- **test_libreoffice_failure**: Mock subprocess to return exit code 1. Assert raises `RuntimeError` containing "conversion failed".

**Code** — Replace `NotImplementedError` stubs in `services/conversion.py`. For `.doc`/`.docx`: write `file_bytes` to temp file in `tempfile.TemporaryDirectory`, run `subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, tmpfile])`, read output PDF, return as `pdf_blob`. Check return code, raise on failure.

**Refactor** — Extract `_convert_to_pdf(file_bytes, extension) -> bytes` helper.

**Commit**: `Convert DOC/DOCX to PDF via LibreOffice`

---

### post-conversion-size-check

**Test** — write these tests and confirm they fail:
- **test_pdf_under_limit**: Process a file producing pdf_blob under 24MB. Assert no error.
- **test_pdf_over_limit**: Mock conversion to return 25MB of bytes. Assert raises `ValueError` containing "exceeds".
- **test_size_check_applies_to_pdf_passthrough**: `process_upload("huge.pdf", large_bytes)` where `large_bytes` > 24MB. Assert raises `ValueError`.

**Code** — After `pdf_blob` is set (for any type that produces one), check `len(pdf_blob) > MAX_PDF_SIZE_BYTES`. Raise `ValueError` if exceeded. Define `MAX_PDF_SIZE_BYTES = 24 * 1024 * 1024`.

**Refactor** — none

**Commit**: `Add post-conversion PDF size validation`

---

## Verification

```bash
# Requires LibreOffice installed: brew install --cask libreoffice

# Create a test .docx (or use an existing one):
cd backend
python -c "
from services.conversion import process_upload
with open('../docs/gc-ai-takehome/test-contract.txt', 'rb') as f:
    txt_bytes = f.read()

# Test TXT still works:
r = process_upload('test.txt', txt_bytes)
print(f'TXT: type={r.upload_type}, text={len(r.text)} chars, pdf_blob={r.pdf_blob}')

# Test DOCX (need a real .docx file):
# r = process_upload('contract.docx', docx_bytes)
# print(f'DOCX: type={r.upload_type}, pdf_blob={len(r.pdf_blob)} bytes')
# Write PDF to verify: open('output.pdf', 'wb').write(r.pdf_blob)
"
```

If a real `.docx` test file is available, convert it and open the resulting PDF to verify
content fidelity visually.
