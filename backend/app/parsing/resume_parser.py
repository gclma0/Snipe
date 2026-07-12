from pathlib import PurePath

from fastapi import HTTPException, status

from app.parsing.docx_parser import parse_docx_resume
from app.parsing.pdf_parser import parse_pdf_resume
from app.parsing.schemas import ResumeParseResult

SUPPORTED_RESUME_EXTENSIONS = {".pdf", ".docx"}


def resume_extension(filename: str) -> str:
    return PurePath(filename).suffix.lower()


def parse_resume(filename: str, content: bytes) -> ResumeParseResult:
    extension = resume_extension(filename)
    if extension == ".pdf":
        return parse_pdf_resume(content)
    if extension == ".docx":
        return parse_docx_resume(content)
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Resume must be a PDF or DOCX file.",
    )
