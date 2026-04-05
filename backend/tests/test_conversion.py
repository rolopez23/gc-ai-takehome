from services.conversion import ConversionResult, process_upload, get_upload_type
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


def test_doc_not_implemented():
    with pytest.raises(NotImplementedError):
        process_upload("file.doc", b"data")


def test_docx_not_implemented():
    with pytest.raises(NotImplementedError):
        process_upload("file.docx", b"data")


def test_case_insensitive():
    result = process_upload("FILE.TXT", b"hello")
    assert result.upload_type == "txt"
