import re

from pydantic import BaseModel, Field

from app.skills.taxonomy import extract_known_skills

PARSER_VERSION = "linkedin-text-parser-v1"


class LinkedInParseResult(BaseModel):
    parser: str = PARSER_VERSION
    source_type: str
    text: str
    text_length: int = Field(ge=0)
    headline: str | None = None
    about: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_items: list[str] = Field(default_factory=list)


def parse_linkedin_text(
    text: str,
    *,
    source_type: str = "linkedin_pasted_text",
) -> LinkedInParseResult:
    cleaned = _compact_lines(text)
    if _looks_like_linkedin_url_only(cleaned):
        raise LinkedInParseError(
            "Direct LinkedIn scraping is not supported. Paste profile text or upload an export/PDF."
        )
    if len(cleaned) < 50:
        raise LinkedInParseError("Paste LinkedIn profile text or upload a PDF/DOCX export.")
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    headline = _first_non_heading_line(lines)
    about = _section_after_heading(lines, {"about", "summary"})
    skills_text = _section_after_heading(lines, {"skills"})
    experience_text = _section_after_heading(lines, {"experience"})
    return LinkedInParseResult(
        source_type=source_type,
        text=cleaned,
        text_length=len(cleaned),
        headline=headline,
        about=about,
        skills=_extract_skills(f"{skills_text or ''}\n{cleaned}"),
        experience_items=_extract_experience_items(experience_text or cleaned),
    )


class LinkedInParseError(RuntimeError):
    pass


def _looks_like_linkedin_url_only(text: str) -> bool:
    compact = text.strip()
    return bool(re.fullmatch(r"https?://(www\.)?linkedin\.com/in/[^\s]+/?", compact))


def _first_non_heading_line(lines: list[str]) -> str | None:
    ignored = {"about", "activity", "experience", "education", "skills", "contact"}
    for line in lines[:8]:
        if line.lower().strip(":") not in ignored and "linkedin.com/in/" not in line.lower():
            return line[:160]
    return None


def _section_after_heading(lines: list[str], headings: set[str]) -> str | None:
    capture = False
    captured: list[str] = []
    stop_headings = {"activity", "experience", "education", "skills", "licenses", "certifications"}
    for line in lines:
        normalized = line.lower().strip(":")
        if normalized in headings:
            capture = True
            continue
        if capture and normalized in stop_headings and normalized not in headings:
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip() or None


def _extract_skills(text: str) -> list[str]:
    return extract_known_skills(text)


def _extract_experience_items(text: str) -> list[str]:
    lines = [line.strip(" -•\t") for line in text.splitlines() if len(line.strip()) >= 12]
    return lines[:8]


def _compact_lines(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(line for line in lines if line).strip()
