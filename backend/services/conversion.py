from dataclasses import dataclass
import functools
import os
import subprocess
import tempfile


@dataclass
class ConversionResult:
    upload_type: str  # "pdf", "txt", "doc", "docx"
    original_blob: bytes  # raw uploaded file
    pdf_blob: bytes | None  # PDF for Claude; None only for txt
    text: str | None  # plain text; set only for txt


SUPPORTED_TYPES = {"txt", "pdf", "doc", "docx"}
MAX_PDF_SIZE_BYTES = 24 * 1024 * 1024  # 24MB, Claude's document block limit


def get_upload_type(filename: str) -> str:
    """Extract and validate the file extension. Return type string without the dot."""
    _, ext = os.path.splitext(filename)
    if not ext:
        raise ValueError(f"Unsupported file type: no extension in '{filename}'")
    ext_lower = ext.lstrip(".").lower()
    if ext_lower not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: .{ext_lower}")
    return ext_lower


@functools.lru_cache
def _find_libreoffice() -> str:
    """Find the LibreOffice binary, checking common paths."""
    for path in [
        "libreoffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "soffice",
    ]:
        if (
            os.path.isfile(path)
            or subprocess.run(["which", path], capture_output=True).returncode == 0
        ):
            return path
    raise RuntimeError(
        "LibreOffice not found. Install with: brew install --cask libreoffice"
    )


def _convert_to_pdf(file_bytes: bytes, extension: str) -> bytes:
    """Convert DOC/DOCX to PDF via LibreOffice headless."""
    libre_bin = _find_libreoffice()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_filename = f"input{extension}"  # e.g. "input.docx"
        input_path = os.path.join(tmpdir, input_filename)
        with open(input_path, "wb") as f:
            f.write(file_bytes)

        result = subprocess.run(
            [
                libre_bin,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                tmpdir,
                input_path,
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed: {result.stderr.decode()}"
            )

        pdf_path = os.path.join(tmpdir, "input.pdf")
        if not os.path.exists(pdf_path):
            raise RuntimeError("LibreOffice conversion produced no output")

        with open(pdf_path, "rb") as f:
            return f.read()


def process_upload(filename: str, file_bytes: bytes) -> ConversionResult:
    """Process an uploaded file and return a ConversionResult."""
    upload_type = get_upload_type(filename)

    if upload_type == "txt":
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(
                "File is not valid UTF-8 text. Save the file as UTF-8 and try again."
            )
        return ConversionResult(
            upload_type="txt",
            original_blob=file_bytes,
            pdf_blob=None,
            text=text,
        )

    pdf_blob: bytes | None = None

    if upload_type == "pdf":
        pdf_blob = file_bytes
    elif upload_type in ("doc", "docx"):
        pdf_blob = _convert_to_pdf(file_bytes, f".{upload_type}")

    if pdf_blob is not None and len(pdf_blob) > MAX_PDF_SIZE_BYTES:
        raise ValueError(
            f"Converted PDF exceeds maximum size ({len(pdf_blob)} bytes > {MAX_PDF_SIZE_BYTES})"
        )

    return ConversionResult(
        upload_type=upload_type,
        original_blob=file_bytes,
        pdf_blob=pdf_blob,
        text=None,
    )
