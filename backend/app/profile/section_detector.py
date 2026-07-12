from collections.abc import Iterable

SECTION_ALIASES: dict[str, set[str]] = {
    "summary": {"summary", "profile", "professional summary", "career summary", "objective"},
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
    },
    "projects": {"projects", "selected projects", "project experience", "portfolio"},
    "education": {"education", "academic background", "qualifications"},
    "skills": {"skills", "technical skills", "core skills", "competencies", "expertise"},
    "certifications": {"certifications", "certificates", "licenses", "credentials"},
}

MAX_HEADING_WORDS = 5


def detect_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_section = "unclassified"
    sections[current_section] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = _section_for_heading(line)
        if heading:
            current_section = heading
            sections.setdefault(current_section, [])
            continue
        sections.setdefault(current_section, []).append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if name != "unclassified" and "\n".join(lines).strip()
    }


def ordered_section_excerpt(sections: dict[str, str], names: Iterable[str]) -> str:
    for name in names:
        value = sections.get(name)
        if value:
            return value
    return ""


def _section_for_heading(line: str) -> str | None:
    normalized = line.lower().strip(":-|")
    if len(normalized.split()) > MAX_HEADING_WORDS:
        return None
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section
    return None
