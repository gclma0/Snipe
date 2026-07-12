from typing import Any

from pydantic import BaseModel, Field

INTERPRETER_VERSION = "deterministic-profile-interpreter-v1"

SPECIALIZATION_KEYWORDS = {
    "software engineering": {
        "python",
        "javascript",
        "typescript",
        "react",
        "fastapi",
        "sql",
        "github",
    },
    "data analytics": {
        "analytics",
        "data analysis",
        "excel",
        "sql",
        "tableau",
        "power bi",
        "looker",
    },
    "finance": {
        "accounting",
        "budgeting",
        "financial modeling",
        "excel",
    },
    "operations": {
        "operations",
        "project management",
        "stakeholder management",
        "customer service",
    },
    "marketing": {
        "marketing",
        "content strategy",
        "sales",
        "communication",
    },
}

SENIORITY_KEYWORDS = {
    "entry": {"intern", "assistant", "junior", "associate"},
    "mid": {"analyst", "specialist", "coordinator", "developer", "manager"},
    "senior": {"senior", "lead", "principal", "director", "head"},
}
SENIORITY_RANK = {"entry": 1, "mid": 2, "senior": 3}


class SpecializationSignal(BaseModel):
    name: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class ProfileInterpretationResult(BaseModel):
    interpreter_version: str = INTERPRETER_VERSION
    primary_specialization: SpecializationSignal | None = None
    secondary_specializations: list[SpecializationSignal] = Field(default_factory=list)
    estimated_seniority: str | None = None
    seniority_confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


def interpret_profile(normalized_profile: dict[str, Any]) -> ProfileInterpretationResult:
    profile_terms = _profile_terms(normalized_profile)
    specialization_scores = []
    for specialization, keywords in SPECIALIZATION_KEYWORDS.items():
        matches = sorted(profile_terms & keywords)
        if matches:
            confidence = min(1.0, len(matches) / max(3, len(keywords) * 0.5))
            specialization_scores.append(
                SpecializationSignal(
                    name=specialization,
                    confidence=round(confidence, 2),
                    evidence=matches[:6],
                )
            )

    specialization_scores.sort(key=lambda item: item.confidence, reverse=True)
    seniority, seniority_confidence, seniority_evidence = _estimate_seniority(normalized_profile)
    return ProfileInterpretationResult(
        primary_specialization=specialization_scores[0] if specialization_scores else None,
        secondary_specializations=specialization_scores[1:3],
        estimated_seniority=seniority,
        seniority_confidence=seniority_confidence,
        evidence=seniority_evidence,
    )


def _profile_terms(normalized_profile: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    skills = normalized_profile.get("skills")
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, dict) and isinstance(skill.get("name"), str):
                terms.add(skill["name"].lower())
            elif isinstance(skill, str):
                terms.add(skill.lower())
    sections = normalized_profile.get("sections")
    if isinstance(sections, dict):
        text = " ".join(str(value).lower() for value in sections.values())
        for keywords in SPECIALIZATION_KEYWORDS.values():
            terms.update(keyword for keyword in keywords if keyword in text)
    return terms


def _estimate_seniority(normalized_profile: dict[str, Any]) -> tuple[str | None, float, list[str]]:
    sections = normalized_profile.get("sections")
    text = (
        " ".join(str(value).lower() for value in sections.values())
        if isinstance(sections, dict)
        else ""
    )
    scores: dict[str, list[str]] = {}
    for level, keywords in SENIORITY_KEYWORDS.items():
        matches = sorted(keyword for keyword in keywords if keyword in text)
        if matches:
            scores[level] = matches
    if not scores:
        return None, 0.0, []
    level = max(scores, key=lambda item: (len(scores[item]), SENIORITY_RANK[item]))
    confidence = min(1.0, len(scores[level]) / 3)
    return level, round(confidence, 2), scores[level]
