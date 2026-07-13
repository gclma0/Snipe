import re
from hashlib import sha256

from app.parsing.schemas import ResumeParseResult
from app.profile.contact_extractor import extract_contact
from app.profile.schemas import EvidenceCandidate, NormalizedProfileBuild
from app.profile.section_detector import detect_sections
from app.skills.taxonomy import extract_known_skills, skill_excerpt

PROFILE_BUILDER_VERSION = "deterministic-profile-builder-v1"

SECTION_FACT_TYPES = {
    "summary": "profile_summary",
    "experience": "experience_section",
    "projects": "projects_section",
    "education": "education_section",
    "skills": "skills_section",
    "certifications": "certifications_section",
}


def build_normalized_profile(
    *,
    parsed: ResumeParseResult,
    profile_id: str,
    source_id: str | None,
) -> NormalizedProfileBuild:
    text = parsed.text
    sections = detect_sections(text)
    contact = extract_contact(text)
    skills = _extract_skills(text, sections.get("skills", ""))
    evidence: list[EvidenceCandidate] = []

    for contact_type, values in contact.items():
        for value in values:
            evidence.append(
                EvidenceCandidate(
                    fact_type=f"contact_{contact_type}",
                    fact_key=_stable_key(f"{contact_type}:{value}"),
                    excerpt=value,
                    normalized_value=value,
                    confidence=0.95,
                    location_json={"source": "resume", "source_id": source_id},
                )
            )

    for section_name, section_text in sections.items():
        evidence.append(
            EvidenceCandidate(
                fact_type=SECTION_FACT_TYPES[section_name],
                fact_key=section_name,
                excerpt=_excerpt(section_text),
                normalized_value=section_name,
                confidence=0.8,
                location_json={"source": "resume", "source_id": source_id},
            )
        )

    for skill in skills:
        evidence.append(
            EvidenceCandidate(
                fact_type="skill",
                fact_key=_stable_key(skill),
                excerpt=_skill_excerpt(skill, text),
                normalized_value=skill,
                confidence=0.75,
                location_json={"source": "resume", "source_id": source_id},
            )
        )

    normalized_json = {
        "schema_version": 1,
        "builder_version": PROFILE_BUILDER_VERSION,
        "profile_id": profile_id,
        "sources": [
            {
                "source_id": source_id,
                "source_type": parsed.source_type,
                "parser": parsed.parser,
                "text_length": parsed.text_length,
            }
        ],
        "contact": contact,
        "sections": {name: _excerpt(value, limit=1200) for name, value in sections.items()},
        "skills": [{"name": skill, "source": "resume", "confidence": 0.75} for skill in skills],
    }
    return NormalizedProfileBuild(normalized_json=normalized_json, evidence=evidence)


def _extract_skills(text: str, skills_section: str) -> list[str]:
    return extract_known_skills(f"{skills_section}\n{text}")


def _skill_excerpt(skill: str, text: str) -> str:
    return skill_excerpt(skill, text)


def _excerpt(value: str, limit: int = 500) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def _stable_key(value: str) -> str:
    return sha256(value.lower().strip().encode("utf-8")).hexdigest()[:16]
