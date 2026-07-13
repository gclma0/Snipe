import re

from app.jobs.schemas import StructuredJobDescription
from app.skills.taxonomy import SKILL_TERMS, SOFT_SKILLS, TOOL_SKILLS

PARSER_VERSION = "deterministic-job-parser-v1"

SENIORITY_TERMS = ("intern", "junior", "associate", "mid", "senior", "lead", "principal", "manager")


def parse_job_description(text: str) -> StructuredJobDescription:
    cleaned = _clean_text(text)
    lines = [line for line in cleaned.splitlines() if line.strip()]
    sections = _section_blocks(lines)
    required_text = _join_sections(
        sections,
        ("requirements", "required qualifications", "must have"),
    )
    preferred_text = _join_sections(
        sections,
        ("preferred qualifications", "nice to have", "preferred"),
    )
    responsibilities_text = _join_sections(
        sections,
        ("responsibilities", "what you will do", "role responsibilities"),
    )
    education_text = _join_sections(sections, ("education", "qualifications"))

    required_skills = _extract_terms(required_text or cleaned, SKILL_TERMS)
    preferred_skills = _extract_terms(preferred_text, SKILL_TERMS)
    tools = _extract_terms(cleaned, TOOL_SKILLS)
    soft_skills = _extract_terms(cleaned, SOFT_SKILLS)
    responsibilities = _extract_bullets(responsibilities_text, limit=8)
    education = _extract_education(education_text or cleaned)
    experience_requirements = _extract_experience_requirements(cleaned)
    seniority = _extract_seniority(cleaned)
    ats_keywords = sorted(set(required_skills + preferred_skills + tools + soft_skills))

    return StructuredJobDescription(
        parser_version=PARSER_VERSION,
        title=_extract_title(lines),
        company=_extract_company(lines),
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        tools=tools,
        soft_skills=soft_skills,
        responsibilities=responsibilities,
        education=education,
        experience_requirements=experience_requirements,
        seniority=seniority,
        ats_keywords=ats_keywords,
    )


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\r", "\n").splitlines())


def _section_blocks(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "overview"
    sections[current] = []
    for line in lines:
        heading = line.lower().strip(":")
        if len(heading.split()) <= 4 and heading in {
            "requirements",
            "required qualifications",
            "must have",
            "preferred",
            "preferred qualifications",
            "nice to have",
            "responsibilities",
            "what you will do",
            "role responsibilities",
            "education",
            "qualifications",
        }:
            current = heading
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _join_sections(sections: dict[str, list[str]], names: tuple[str, ...]) -> str:
    return "\n".join(line for name in names for line in sections.get(name, []))


def _extract_terms(text: str, terms: set[str]) -> list[str]:
    haystack = text.lower()
    return sorted(
        term
        for term in terms
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", haystack)
    )


def _extract_bullets(text: str, limit: int) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip(" -•\t")
        if len(cleaned.split()) >= 4:
            bullets.append(cleaned)
        if len(bullets) == limit:
            break
    return bullets


def _extract_education(text: str) -> list[str]:
    matches = re.findall(
        r"\b(?:bachelor|master|phd|degree|diploma|certification|certified)\b[^.\n]*",
        text,
        flags=re.IGNORECASE,
    )
    return sorted({match.strip() for match in matches})


def _extract_experience_requirements(text: str) -> list[str]:
    matches = re.findall(r"\b\d+\+?\s+years?[^.\n]*", text, flags=re.IGNORECASE)
    return sorted({match.strip() for match in matches})


def _extract_seniority(text: str) -> str | None:
    lowered = text.lower()
    for term in SENIORITY_TERMS:
        if re.search(rf"(?<![a-z0-9]){term}(?![a-z0-9])", lowered):
            return term
    return None


def _extract_title(lines: list[str]) -> str | None:
    for line in lines[:5]:
        if 2 <= len(line.split()) <= 8 and not line.lower().startswith(("about ", "company ")):
            return line.strip()
    return None


def _extract_company(lines: list[str]) -> str | None:
    for line in lines[:8]:
        match = re.search(r"company\s*:\s*(.+)", line, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
