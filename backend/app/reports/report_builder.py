import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from app.scoring.readiness import ReadinessDashboardResult, build_readiness_dashboard

REPORT_TYPE = "mvp_basic_report"
REPORT_VERSION = "mvp-basic-report-v1"


class BasicReportResult(BaseModel):
    report_type: str = REPORT_TYPE
    report_version: str = REPORT_VERSION
    title: str
    summary: str
    readiness: ReadinessDashboardResult
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    markdown: str


def build_basic_report(
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any] | None = None,
) -> BasicReportResult:
    readiness = build_readiness_dashboard(normalized_profile, structured_job)
    title = _title(readiness)
    strengths = _strengths(normalized_profile, readiness)
    weaknesses = _weaknesses(readiness)
    skill_gaps = (
        [item.skill for item in readiness.skill_gap.missing_skills[:8]]
        if readiness.skill_gap
        else []
    )
    summary = _summary(readiness)
    markdown = _markdown(
        title=title,
        summary=summary,
        readiness=readiness,
        strengths=strengths,
        weaknesses=weaknesses,
        skill_gaps=skill_gaps,
    )
    return BasicReportResult(
        title=title,
        summary=summary,
        readiness=readiness,
        strengths=strengths,
        weaknesses=weaknesses,
        skill_gaps=skill_gaps,
        markdown=markdown,
    )


def report_input_hash(
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any] | None,
) -> str:
    encoded = json.dumps(
        {"profile": normalized_profile, "job": structured_job or {}, "version": REPORT_VERSION},
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _title(readiness: ReadinessDashboardResult) -> str:
    specialization = readiness.interpretation.primary_specialization
    if specialization:
        return f"Snipe Career Report: {specialization.name.title()}"
    return "Snipe Career Report"


def _summary(readiness: ReadinessDashboardResult) -> str:
    specialization = readiness.interpretation.primary_specialization
    specialization_text = specialization.name if specialization else "the current profile"
    seniority = readiness.interpretation.estimated_seniority or "unspecified seniority"
    return (
        f"Overall readiness is {readiness.scores.overall}/100 for {specialization_text} "
        f"with estimated {seniority} positioning."
    )


def _strengths(
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
) -> list[str]:
    strengths: list[str] = []
    if readiness.interpretation.primary_specialization:
        specialization = readiness.interpretation.primary_specialization.name
        strengths.append(f"Detected specialization: {specialization}.")
    if readiness.scores.resume_quality >= 80:
        strengths.append("Resume quality signals are strong for the current MVP checks.")
    if readiness.scores.profile_completeness >= 80:
        strengths.append("Profile completeness is strong enough for downstream matching.")
    skills = normalized_profile.get("skills")
    if isinstance(skills, list) and skills:
        names = [item.get("name") for item in skills if isinstance(item, dict) and item.get("name")]
        if names:
            strengths.append(f"Extracted reusable skills include {', '.join(names[:5])}.")
    return strengths[:5]


def _weaknesses(readiness: ReadinessDashboardResult) -> list[str]:
    weaknesses: list[str] = []
    if readiness.scores.resume_quality < 80:
        weaknesses.append("Resume quality needs improvement before relying on downstream outputs.")
    if readiness.scores.ats_readiness < 80:
        weaknesses.append("Snipe ATS Readiness is below the preferred MVP threshold.")
    if readiness.scores.profile_completeness < 80:
        weaknesses.append("Profile completeness is missing useful evidence or sections.")
    if readiness.scores.skill_alignment is not None and readiness.scores.skill_alignment < 70:
        weaknesses.append("Skill alignment to the selected target job is limited.")
    return weaknesses[:5]


def _markdown(
    *,
    title: str,
    summary: str,
    readiness: ReadinessDashboardResult,
    strengths: list[str],
    weaknesses: list[str],
    skill_gaps: list[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Summary",
        summary,
        "",
        "## Scores",
        f"- Overall readiness: {readiness.scores.overall}",
        f"- Resume quality: {readiness.scores.resume_quality}",
        f"- Snipe ATS readiness: {readiness.scores.ats_readiness}",
        f"- Profile completeness: {readiness.scores.profile_completeness}",
    ]
    if readiness.scores.skill_alignment is not None:
        lines.append(f"- Skill alignment: {readiness.scores.skill_alignment}")
    lines.extend(["", "## Strengths"])
    lines.extend([f"- {item}" for item in strengths] or ["- No major strengths detected yet."])
    lines.extend(["", "## Improvement Areas"])
    lines.extend([f"- {item}" for item in weaknesses] or ["- No major improvement areas detected."])
    lines.extend(["", "## Skill Gaps"])
    lines.extend(
        [f"- {item}" for item in skill_gaps] or ["- Add a target job to calculate skill gaps."]
    )
    return "\n".join(lines)
