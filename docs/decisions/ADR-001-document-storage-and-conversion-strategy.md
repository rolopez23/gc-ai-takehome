# ADR-001: Document Storage and Conversion Strategy

## Status
Accepted

## Date
2026-04-05

## Context
M3 moves contract evaluation from frontend-only to backend-driven. The backend must accept file
uploads in PDF, TXT, DOC, and DOCX formats, send them to the Anthropic API for analysis, and
persist both the original document and the evaluation results.

Key constraints:
- Claude's API natively accepts PDF as a `document` content block (base64-encoded) with full
  fidelity — tables, formatting, headers are all preserved
- Claude's API does NOT accept DOC or DOCX formats
- Text extraction from DOC/DOCX loses formatting, table structure, and layout information that
  is material to contract interpretation
- Lawyers heavily use Word formats (.doc and .docx) — both are must-haves

## Decision
**Option C: Convert DOC/DOCX to PDF, send PDF to Claude. Store both the original file blob and
the converted PDF blob.**

### Storage model
Each contract record stores:
- `original_blob` — the raw uploaded file (PDF, TXT, DOC, or DOCX bytes)
- `pdf_blob` — the PDF conversion result (NULL for PDF and TXT uploads)
- `upload_type` — the original file extension (`pdf`, `txt`, `doc`, `docx`)

The `upload_type` field makes the absence of `pdf_blob` deterministic:
- `pdf` → `pdf_blob` is NULL (the original IS the PDF)
- `txt` → `pdf_blob` is NULL (sent as text, no PDF needed)
- `doc` → `pdf_blob` is populated (converted via LibreOffice)
- `docx` → `pdf_blob` is populated (converted via LibreOffice)

### What gets sent to Claude
| Upload type | Sent to Claude as |
|-------------|-------------------|
| `txt` | Text content in message body |
| `pdf` | `document` content block (base64 of `original_blob`) |
| `doc` | `document` content block (base64 of `pdf_blob`) |
| `docx` | `document` content block (base64 of `pdf_blob`) |

### Conversion
DOC and DOCX files are converted to PDF via `libreoffice --headless --convert-to pdf`. This is
the single system dependency for file conversion and handles both legacy and modern Word formats.

## Alternatives Considered

### Option A: Text extraction only
- **Approach**: `pdfplumber` for PDF, `python-docx` for DOCX, `antiword` for DOC — extract plain text, send as text to Claude
- **Pros**: No heavy system dependencies, simpler pipeline
- **Cons**: Loses formatting, table structure, headers, columns — all material to contract analysis. Claude sees degraded input.
- **Rejected**: Information loss is unacceptable for legal document analysis

### Option B: Convert DOC/DOCX to PDF, discard originals
- **Approach**: Same conversion as Option C, but only store the PDF
- **Pros**: Simpler storage, one canonical format
- **Cons**: Cannot serve back the original Word file; lossy if user wants to download what they uploaded
- **Rejected**: Keeping originals is cheap and enables future "download original" functionality

### Send DOC/DOCX raw bytes to Claude
- Not possible — the API does not accept Word formats

### OpenAI file inputs for DOC/DOCX extraction
- **Approach**: Use OpenAI's Chat Completions API file input to extract text from DOC/DOCX, then send text to Claude for evaluation (or use OpenAI end-to-end)
- **Pros**: Zero system dependencies, no LibreOffice in Docker
- **Cons**: Non-deterministic extraction (LLM-based, not a fixed conversion), tables/formatting may be lost, OpenAI's own docs recommend converting to PDF for fidelity
- **Status**: Known alternative. If LibreOffice proves painful in Docker, this is the fallback. Fidelity loss is likely minimal for mostly-text contracts.
- **Ref**: https://developers.openai.com/api/docs/guides/file-inputs

## Consequences
- LibreOffice (~500MB) must be in the Docker image / development environment
- Two blob columns per contract increases storage, but contracts are small documents
- The `upload_type` field serves as the discriminator for which blob to send to Claude and whether `pdf_blob` should exist
- Text extraction can be added later as a search/indexing optimization without changing the primary evaluation path
