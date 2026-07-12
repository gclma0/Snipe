import fitz

from app.parsing.schemas import ResumeParseResult

PARSER_VERSION = "pymupdf-v1"


def parse_pdf_resume(content: bytes) -> ResumeParseResult:
    text_parts: list[str] = []
    with fitz.open(stream=content, filetype="pdf") as document:
        for page in document:
            text_parts.append(page.get_text("text"))
        text = "\n".join(part.strip() for part in text_parts if part.strip())
        return ResumeParseResult(
            parser=PARSER_VERSION,
            source_type="resume_pdf",
            text=text,
            text_length=len(text),
            page_count=document.page_count,
        )
