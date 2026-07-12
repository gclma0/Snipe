import json
import re
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, Field

ANALYSIS_TYPE = "resume_quality"
DETERMINISTIC_VERSION = "resume-quality-rules-v1"

Severity = Literal["info", "low", "medium", "high"]

ACTION_VERBS = {
    "achieved",
    "analyzed",
    "built",
    "coordinated",
    "created",
    "delivered",
    "designed",
    "developed",
    "improved",
    "increased",
    "led",
    "managed",
    "optimized",
    "reduced",
    "resolved",
    "supported",
}

REQUIRED_SECTIONS = {
    "summary": "Add a concise summary section.",
    "experience": "Add a work experience section with role evidence.",
    "skills": "Add a skills section that matches the target role.",
    "education": "Add an education or qualifications section when applicable.",
}


class ResumeQualityFinding(BaseModel):
    code: str
    severity: Severity
    title: str
    detail: str
    recommendation: str


class ResumeQualityResult(BaseModel):
    analysis_type: str = ANALYSIS_TYPE
    deterministic_version: str = DETERMINISTIC_VERSION
    score: int = Field(ge=0, le=100)
    findings: list[ResumeQualityFinding]
    checks: dict[str, bool]


def analyze_resume_quality(normalized_profile: dict[str, Any]) -> ResumeQualityResult:
    findings: list[ResumeQualityFinding] = []
    checks: dict[str, bool] = {}
    contact_value = normalized_profile.get("contact")
    sections_value = normalized_profile.get("sections")
    skills_value = normalized_profile.get("skills")
    contact = contact_value if isinstance(contact_value, dict) else {}
    sections = sections_value if isinstance(sections_value, dict) else {}
    skills = skills_value if isinstance(skills_value, list) else []

    checks["has_email"] = bool(contact.get("emails"))
    if not checks["has_email"]:
        findings.append(
            _finding(
                "missing_email",
                "high",
                "Email is missing",
                "The normalized resume profile does not include an email address.",
                "Add a professional email address near the top of the resume.",
            )
        )

    checks["has_phone"] = bool(contact.get("phones"))
    if not checks["has_phone"]:
        findings.append(
            _finding(
                "missing_phone",
                "medium",
                "Phone number is missing",
                "The normalized resume profile does not include a phone number.",
                "Add one reachable phone number near the contact details.",
            )
        )

    for section, recommendation in REQUIRED_SECTIONS.items():
        check_name = f"has_{section}_section"
        checks[check_name] = bool(sections.get(section))
        if not checks[check_name]:
            findings.append(
                _finding(
                    f"missing_{section}",
                    "high" if section in {"experience", "skills"} else "medium",
                    f"{section.title()} section is missing",
                    f"The normalized profile does not include a {section} section.",
                    recommendation,
                )
            )

    summary = str(sections.get("summary") or "")
    checks["summary_is_concise"] = not summary or 80 <= len(summary) <= 700
    if summary and not checks["summary_is_concise"]:
        findings.append(
            _finding(
                "summary_length",
                "low",
                "Summary length needs adjustment",
                "The summary appears unusually short or long for a resume profile.",
                "Use two to four lines focused on role, strengths, and target direction.",
            )
        )

    checks["has_three_or_more_skills"] = len(skills) >= 3
    if not checks["has_three_or_more_skills"]:
        findings.append(
            _finding(
                "thin_skills",
                "medium",
                "Skills section has limited extracted skills",
                "Fewer than three recognizable skills were extracted from the resume.",
                "Add role-relevant tools, methods, domain skills, and transferable skills.",
            )
        )

    experience = str(sections.get("experience") or "")
    checks["experience_uses_action_verbs"] = _has_action_verb(experience)
    if experience and not checks["experience_uses_action_verbs"]:
        findings.append(
            _finding(
                "weak_experience_language",
                "medium",
                "Experience wording could be stronger",
                "The experience section has limited evidence of action-oriented bullet wording.",
                "Start impact bullets with clear verbs such as led, built, managed, or improved.",
            )
        )

    checks["experience_has_quantified_signal"] = bool(re.search(r"\b\d+[%+]?\b", experience))
    if experience and not checks["experience_has_quantified_signal"]:
        findings.append(
            _finding(
                "missing_quantified_results",
                "low",
                "Quantified results are limited",
                "The experience section does not include obvious numeric outcome signals.",
                "Add truthful numbers where available, such as volume, time, budget, or quality.",
            )
        )

    score = _score(findings)
    return ResumeQualityResult(score=score, findings=findings, checks=checks)


def analysis_input_hash(normalized_profile: dict[str, Any]) -> str:
    encoded = json.dumps(normalized_profile, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _finding(
    code: str,
    severity: Severity,
    title: str,
    detail: str,
    recommendation: str,
) -> ResumeQualityFinding:
    return ResumeQualityFinding(
        code=code,
        severity=severity,
        title=title,
        detail=detail,
        recommendation=recommendation,
    )


def _has_action_verb(value: str) -> bool:
    words = {word.lower() for word in re.findall(r"[A-Za-z]+", value)}
    return bool(words & ACTION_VERBS)


def _score(findings: list[ResumeQualityFinding]) -> int:
    penalties = {"high": 16, "medium": 10, "low": 5, "info": 0}
    return max(0, 100 - sum(penalties[finding.severity] for finding in findings))
