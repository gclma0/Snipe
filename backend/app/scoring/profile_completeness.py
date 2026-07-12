from typing import Any

from app.scoring.common import DeterministicScoreResult, ScoreFinding, finding, score_from_findings

ANALYSIS_TYPE = "profile_completeness"
DETERMINISTIC_VERSION = "profile-completeness-v1"


def analyze_profile_completeness(normalized_profile: dict[str, Any]) -> DeterministicScoreResult:
    findings: list[ScoreFinding] = []
    checks: dict[str, bool] = {}
    contact = _dict_value(normalized_profile, "contact")
    sections = _dict_value(normalized_profile, "sections")
    skills = _list_value(normalized_profile, "skills")
    sources = _list_value(normalized_profile, "sources")

    expectations = {
        "contact": bool(contact.get("emails") and contact.get("phones")),
        "summary": bool(sections.get("summary")),
        "experience": bool(sections.get("experience")),
        "skills": len(skills) >= 5,
        "education": bool(sections.get("education")),
        "source": bool(sources),
    }
    checks.update({f"has_{key}": value for key, value in expectations.items()})

    if not expectations["contact"]:
        findings.append(
            finding(
                "profile_contact_incomplete",
                "high",
                "Contact details are incomplete",
                "The profile needs both email and phone contact fields for the MVP baseline.",
                "Add accurate contact details to the resume before re-uploading.",
            )
        )

    for section in ("summary", "experience", "education"):
        if not expectations[section]:
            findings.append(
                finding(
                    f"profile_missing_{section}",
                    "medium",
                    f"{section.title()} data is missing",
                    f"The normalized profile does not include {section} data.",
                    f"Add a clear {section} section when it applies to your profession.",
                )
            )

    if not expectations["skills"]:
        findings.append(
            finding(
                "profile_skills_incomplete",
                "medium",
                "Skill data is incomplete",
                "The profile has fewer than five normalized skills.",
                "Add truthful technical, domain, or transferable skills.",
            )
        )

    if not expectations["source"]:
        findings.append(
            finding(
                "profile_source_missing",
                "high",
                "Resume source is missing",
                "The profile is not linked to a parsed resume source.",
                "Upload a resume so the profile can cite evidence.",
            )
        )

    return DeterministicScoreResult(
        analysis_type=ANALYSIS_TYPE,
        deterministic_version=DETERMINISTIC_VERSION,
        score=score_from_findings(findings),
        findings=findings,
        checks=checks,
    )


def _dict_value(value: dict[str, Any], key: str) -> dict[str, Any]:
    item = value.get(key)
    return item if isinstance(item, dict) else {}


def _list_value(value: dict[str, Any], key: str) -> list[Any]:
    item = value.get(key)
    return item if isinstance(item, list) else []
