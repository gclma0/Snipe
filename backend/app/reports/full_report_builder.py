import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from app.reports.report_builder import build_basic_report

FULL_REPORT_TYPE = "full_career_report"
FULL_REPORT_VERSION = "full-career-report-v1"


class FullCareerReportResult(BaseModel):
    report_type: str = FULL_REPORT_TYPE
    report_version: str = FULL_REPORT_VERSION
    title: str
    summary: str
    sections_included: list[str] = Field(default_factory=list)
    markdown: str


def build_full_career_report(
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any] | None,
    generated_outputs: list[dict[str, Any]],
) -> FullCareerReportResult:
    basic = build_basic_report(normalized_profile, structured_job)
    sections = ["readiness", "strengths", "skill_gaps"]
    lines = [
        basic.markdown,
        "",
        "## Saved AI Outputs",
    ]
    if not generated_outputs:
        lines.append("- No saved AI outputs are available yet.")
    for output in generated_outputs:
        output_type = str(output.get("output_type") or "generated_output")
        markdown = output.get("result_markdown")
        raw_result_json = output.get("result_json")
        result_json = raw_result_json if isinstance(raw_result_json, dict) else {}
        title = _section_title(output_type)
        sections.append(output_type)
        lines.extend(["", f"### {title}"])
        if isinstance(markdown, str) and markdown.strip():
            lines.append(markdown.strip())
        elif isinstance(result_json, dict) and result_json.get("summary"):
            lines.append(str(result_json["summary"]))
        else:
            lines.append("Saved output exists, but no readable summary is available.")

    summary = (
        f"Full career report includes {len(sections)} sections using deterministic analysis "
        "and saved generated outputs."
    )
    return FullCareerReportResult(
        title=basic.title.replace("Career Report", "Full Career Report"),
        summary=summary,
        sections_included=sections,
        markdown="\n".join(lines).strip(),
    )


def full_report_input_hash(
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any] | None,
    generated_outputs: list[dict[str, Any]],
) -> str:
    encoded = json.dumps(
        {
            "profile": normalized_profile,
            "job": structured_job or {},
            "output_ids": [output.get("id") for output in generated_outputs],
            "version": FULL_REPORT_VERSION,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _section_title(output_type: str) -> str:
    labels = {
        "ai_interview_prep": "Interview Questions",
        "ai_claim_verification_questions": "Claim Questions",
        "ai_outreach_message_pack": "Outreach Messages",
        "ai_career_transition_analysis": "Career Transition",
        "ai_project_roadmap_recommendations": "Projects And Roadmap",
        "ai_application_materials": "Application Materials",
        "ai_resume_tailoring_package": "Resume Tailoring",
        "ai_resume_rewrite_suggestions": "Resume Rewrite Suggestions",
        "job_match": "Job Matches",
    }
    return labels.get(output_type, output_type.replace("_", " ").title())
