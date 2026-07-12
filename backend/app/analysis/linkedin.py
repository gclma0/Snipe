from hashlib import sha256

from pydantic import BaseModel, Field

from app.parsing.linkedin_parser import LinkedInParseResult
from app.profile.schemas import EvidenceCandidate

ANALYSIS_VERSION = "linkedin-profile-analysis-v1"


class LinkedInAnalysisResult(BaseModel):
    analysis_version: str = ANALYSIS_VERSION
    source_type: str
    headline: str | None = None
    about_excerpt: str | None = None
    skill_signals: list[str] = Field(default_factory=list)
    experience_items: list[str] = Field(default_factory=list)
    text_length: int = Field(ge=0)
    signals: dict[str, bool] = Field(default_factory=dict)


def analyze_linkedin_profile(parsed: LinkedInParseResult) -> LinkedInAnalysisResult:
    return LinkedInAnalysisResult(
        source_type=parsed.source_type,
        headline=parsed.headline,
        about_excerpt=_excerpt(parsed.about or ""),
        skill_signals=parsed.skills,
        experience_items=parsed.experience_items[:5],
        text_length=parsed.text_length,
        signals={
            "has_headline": bool(parsed.headline),
            "has_about": bool(parsed.about),
            "has_skills": bool(parsed.skills),
            "has_experience": bool(parsed.experience_items),
        },
    )


def linkedin_evidence(
    *,
    profile_id: str,
    source_id: str | None,
    analysis: LinkedInAnalysisResult,
) -> list[EvidenceCandidate]:
    evidence: list[EvidenceCandidate] = []
    if analysis.headline:
        evidence.append(
            EvidenceCandidate(
                fact_type="linkedin_headline",
                fact_key=_stable_key(analysis.headline),
                excerpt=analysis.headline,
                normalized_value=analysis.headline,
                confidence=0.7,
                location_json={
                    "source": "linkedin",
                    "profile_id": profile_id,
                    "source_id": source_id,
                },
            )
        )
    for skill in analysis.skill_signals:
        evidence.append(
            EvidenceCandidate(
                fact_type="linkedin_skill",
                fact_key=_stable_key(skill),
                excerpt=f"LinkedIn profile includes {skill}.",
                normalized_value=skill,
                confidence=0.65,
                location_json={
                    "source": "linkedin",
                    "profile_id": profile_id,
                    "source_id": source_id,
                },
            )
        )
    for item in analysis.experience_items:
        evidence.append(
            EvidenceCandidate(
                fact_type="linkedin_experience",
                fact_key=_stable_key(item),
                excerpt=_excerpt(item),
                normalized_value=_excerpt(item, limit=120),
                confidence=0.6,
                location_json={
                    "source": "linkedin",
                    "profile_id": profile_id,
                    "source_id": source_id,
                },
            )
        )
    return evidence


def _excerpt(value: str, limit: int = 500) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3].rstrip()}..."


def _stable_key(value: str) -> str:
    return sha256(value.lower().strip().encode("utf-8")).hexdigest()[:16]
