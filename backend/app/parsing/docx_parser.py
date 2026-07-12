from io import BytesIO

from docx import Document

from app.parsing.schemas import ResumeParseResult

PARSER_VERSION = "python-docx-v1"


def parse_docx_resume(content: bytes) -> ResumeParseResult:
    document = Document(BytesIO(content))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    text = "\n".join(paragraph for paragraph in paragraphs if paragraph)
    return ResumeParseResult(
        parser=PARSER_VERSION,
        source_type="resume_docx",
        text=text,
        text_length=len(text),
        paragraph_count=len([paragraph for paragraph in paragraphs if paragraph]),
    )
