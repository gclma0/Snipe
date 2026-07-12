import re
from typing import Any

from app.scoring.common import DeterministicScoreResult, ScoreFinding, finding, score_from_findings

ANALYSIS_TYPE = "ats_readiness"
DETERMINISTIC_VERSION = "snipe-ats-readiness-v1"


def analyze_ats_readiness(normalized_profile: dict[str, Any]) -> DeterministicScoreResult:
    findings: list[ScoreFinding] = []
    checks: dict[str, bool] = {}
    contact = _dict_value(normalized_profile, "contact")
    sections = _dict_value(normalized_profile, "sections")
    skills = _list_value(normalized_profile, "skills")
    source_text = " ".join(str(value) for value in sections.values())

    checks["has_email"] = bool(contact.get("emails"))
    if not checks["has_email"]:
        findings.append(
            finding(
                "ats_missing_email",
                "high",
                "Email is missing",
                "Snipe did not find an email address in the normalized resume profile.",
                "Add a professional email address in the resume header.",
            )
        )

    checks["has_phone"] = bool(contact.get("phones"))
    if not checks["has_phone"]:
        findings.append(
            finding(
                "ats_missing_phone",
                "medium",
                "Phone number is missing",
                "Snipe did not find a phone number in the normalized resume profile.",
                "Add one reachable phone number in the resume header.",
            )
        )

    checks["has_standard_sections"] = all(
        bool(sections.get(section)) for section in ("summary", "experience", "skills")
    )
    if not checks["has_standard_sections"]:
        findings.append(
            finding(
                "ats_missing_standard_sections",
                "high",
                "Core resume sections are incomplete",
                "Snipe expects summary, experience, and skills sections for baseline readiness.",
                "Use clear section headings such as Summary, Experience, Skills, and Education.",
            )
        )

    checks["has_parseable_skills"] = len(skills) >= 5
    if not checks["has_parseable_skills"]:
        findings.append(
            finding(
                "ats_thin_skill_keywords",
                "medium",
                "Skill keyword coverage is thin",
                "Fewer than five normalized skills were found.",
                "Add truthful role-relevant skills, tools, methods, and domain keywords.",
            )
        )

    experience = str(sections.get("experience") or "")
    checks["has_quantified_experience"] = bool(re.search(r"\b\d+[%+]?\b", experience))
    if sections.get("experience") and not checks["has_quantified_experience"]:
        findings.append(
            finding(
                "ats_no_quantified_experience",
                "low",
                "Experience has limited numeric signals",
                "No clear numeric results were found in the experience section.",
                "Add accurate numbers where available, such as scale, volume, time, or budget.",
            )
        )

    checks["avoids_table_like_text"] = not _looks_table_heavy(source_text)
    if not checks["avoids_table_like_text"]:
        findings.append(
            finding(
                "ats_table_like_layout",
                "medium",
                "Resume text appears table-heavy",
                "The extracted text has repeated separators that may indicate layout issues.",
                "Prefer simple headings and text blocks over table-heavy resume formatting.",
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


def _looks_table_heavy(value: str) -> bool:
    if not value:
        return False
    separators = value.count("|") + value.count("\t")
    return separators >= 8
