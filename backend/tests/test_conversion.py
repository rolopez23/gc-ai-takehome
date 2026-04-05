from services.conversion import ConversionResult, process_upload, get_upload_type
from unittest.mock import patch, MagicMock
import os
import pytest


def test_process_txt():
    result = process_upload("contract.txt", b"Hello world")
    assert result.upload_type == "txt"
    assert result.text == "Hello world"
    assert result.pdf_blob is None
    assert result.original_blob == b"Hello world"


def test_process_txt_utf8():
    raw = "résumé clause §3".encode("utf-8")
    result = process_upload("contract.txt", raw)
    assert result.text == "résumé clause §3"


def test_process_pdf():
    result = process_upload("contract.pdf", b"fake-pdf")
    assert result.upload_type == "pdf"
    assert result.pdf_blob == b"fake-pdf"
    assert result.text is None
    assert result.original_blob == b"fake-pdf"


def test_reject_png():
    with pytest.raises(ValueError, match="(?i)unsupported"):
        process_upload("image.png", b"data")


def test_reject_no_extension():
    with pytest.raises(ValueError):
        process_upload("noext", b"data")


def test_process_docx():
    """Mock LibreOffice to return a fake PDF."""
    fake_pdf = b"%PDF-1.4 fake pdf content"

    def mock_run(cmd, **kwargs):
        outdir = cmd[cmd.index("--outdir") + 1]
        pdf_path = os.path.join(outdir, "input.pdf")
        with open(pdf_path, "wb") as f:
            f.write(fake_pdf)
        mock_result = MagicMock()
        mock_result.returncode = 0
        return mock_result

    with patch("services.conversion._find_libreoffice", return_value="libreoffice"), \
         patch("services.conversion.subprocess.run", side_effect=mock_run):
        result = process_upload("contract.docx", b"fake-docx-bytes")

    assert result.upload_type == "docx"
    assert result.pdf_blob == fake_pdf
    assert result.text is None
    assert result.original_blob == b"fake-docx-bytes"


def test_process_doc():
    """Mock LibreOffice to return a fake PDF for .doc files."""
    fake_pdf = b"%PDF-1.4 fake pdf content"

    def mock_run(cmd, **kwargs):
        outdir = cmd[cmd.index("--outdir") + 1]
        pdf_path = os.path.join(outdir, "input.pdf")
        with open(pdf_path, "wb") as f:
            f.write(fake_pdf)
        mock_result = MagicMock()
        mock_result.returncode = 0
        return mock_result

    with patch("services.conversion._find_libreoffice", return_value="libreoffice"), \
         patch("services.conversion.subprocess.run", side_effect=mock_run):
        result = process_upload("contract.doc", b"fake-doc-bytes")

    assert result.upload_type == "doc"
    assert result.pdf_blob == fake_pdf
    assert result.text is None
    assert result.original_blob == b"fake-doc-bytes"


def test_libreoffice_failure():
    """Mock subprocess to return non-zero exit code."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = b"some error"

    with patch("services.conversion._find_libreoffice", return_value="libreoffice"), \
         patch("services.conversion.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="conversion failed"):
            process_upload("file.docx", b"data")


def test_pdf_over_size_limit():
    """PDF blob exceeding 24MB raises ValueError."""
    oversized = b"x" * (24 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="exceeds"):
        process_upload("big.pdf", oversized)


def test_pdf_under_size_limit():
    """Normal size PDF passes without error."""
    result = process_upload("normal.pdf", b"small-pdf")
    assert result.upload_type == "pdf"
    assert result.pdf_blob == b"small-pdf"


def test_case_insensitive():
    result = process_upload("FILE.TXT", b"hello")
    assert result.upload_type == "txt"
