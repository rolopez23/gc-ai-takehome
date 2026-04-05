from dataclasses import dataclass
import os


@dataclass
class ConversionResult:
    upload_type: str          # "pdf", "txt", "doc", "docx"
    original_blob: bytes      # raw uploaded file
    pdf_blob: bytes | None    # PDF for Claude; None only for txt
    text: str | None          # plain text; set only for txt


SUPPORTED_TYPES = {"txt", "pdf", "doc", "docx"}


def get_upload_type(filename: str) -> str:
    """Extract and validate the file extension. Return type string without the dot."""
    _, ext = os.path.splitext(filename)
    if not ext:
        raise ValueError(f"Unsupported file type: no extension in '{filename}'")
    ext_lower = ext.lstrip(".").lower()
    if ext_lower not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: .{ext_lower}")
    return ext_lower


def process_upload(filename: str, file_bytes: bytes) -> ConversionResult:
    """Process an uploaded file and return a ConversionResult."""
    upload_type = get_upload_type(filename)

    if upload_type == "txt":
        return ConversionResult(
            upload_type="txt",
            original_blob=file_bytes,
            pdf_blob=None,
            text=file_bytes.decode("utf-8"),
        )

    if upload_type == "pdf":
        return ConversionResult(
            upload_type="pdf",
            original_blob=file_bytes,
            pdf_blob=file_bytes,
            text=None,
        )

    # doc / docx
    raise NotImplementedError("LibreOffice conversion not yet implemented")
