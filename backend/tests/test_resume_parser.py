from io import BytesIO

import fitz
from docx import Document

from app.parsing.resume_parser import parse_resume


def make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def make_docx(text: str) -> bytes:
    buffer = BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def test_parse_pdf_resume_extracts_text_and_page_count() -> None:
    result = parse_resume("resume.pdf", make_pdf("Python Developer"))

    assert result.source_type == "resume_pdf"
    assert result.page_count == 1
    assert "Python Developer" in result.text


def test_parse_docx_resume_extracts_text_and_paragraph_count() -> None:
    result = parse_resume("resume.docx", make_docx("Operations Manager"))

    assert result.source_type == "resume_docx"
    assert result.paragraph_count == 1
    assert "Operations Manager" in result.text
