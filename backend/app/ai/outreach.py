import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from app.scoring.readiness import ReadinessDashboardResult

OUTREACH_VERSION = "deterministic-outreach-v1"
OUTREACH_CONTEXT_VERSION = "deterministic-outreach-context-v1"


class OutreachMessagePack(BaseModel):
    output_type: str = "ai_outreach_message_pack"
    output_version: str = OUTREACH_VERSION
    provider: str = "deterministic"
    model_name: str = "deterministic-outreach-v1"
    summary: str
    linkedin_connection_message: str
    recruiter_outreach_message: str
    job_application_email: str
    follow_up_email: str
    interview_thank_you_email: str
    referral_request: str
    short_professional_intro: str
    evidence_used: list[str] = Field(default_factory=list, max_length=8)
    missing_evidence_warnings: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


def build_outreach_context(
    *,
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "context_version": OUTREACH_CONTEXT_VERSION,
        "verified_skills": _skill_names(normalized_profile),
        "experience_signals": _experience_signals(normalized_profile),
        "target_job": _job_summary(structured_job),
        "readiness": {
            "primary_specialization": (
                readiness.interpretation.primary_specialization.name
                if readiness.interpretation.primary_specialization
                else None
            ),
            "estimated_seniority": readiness.interpretation.estimated_seniority,
        },
        "constraints": [
            "Use verified skills and compact experience signals only.",
            "Use placeholders for recipient, company, job title, and unverified details.",
            "Do not invent achievements, metrics, employers, credentials, or experience.",
        ],
    }


def outreach_context_hash(context: dict[str, Any]) -> str:
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def generate_outreach_message_pack(context: dict[str, Any]) -> OutreachMessagePack:
    skills = _string_list(context.get("verified_skills"))
    experience = _string_list(context.get("experience_signals"))
    target_job = context.get("target_job") if isinstance(context.get("target_job"), dict) else {}
    role = str(target_job.get("title") or "[target role]")
    company = str(target_job.get("company") or "[company]")
    skill_text = ", ".join(skills[:3]) if skills else "[verified skills]"
    evidence = experience[0] if experience else "[verified experience example]"
    intro = (
        f"I am a candidate focused on {role}, with verified experience around {skill_text}. "
        f"One profile-supported example is: {evidence}."
    )
    warnings = []
    if not skills:
        warnings.append(
            "No verified skills were found; keep outreach general until skills are supported."
        )
    if not experience:
        warnings.append(
            "No specific experience signal was found; add a truthful example before sending."
        )
    return OutreachMessagePack(
        summary="Outreach message pack generated from verified profile evidence.",
        linkedin_connection_message=(
            f"Hi [name], I am exploring {role} opportunities and noticed your work at {company}. "
            f"My background includes {skill_text}. I would value connecting and learning more "
            "about your team."
        ),
        recruiter_outreach_message=(
            f"Hi [recruiter name], I am interested in {role} roles. {intro} If useful, I can "
            "share my resume and discuss fit for current openings."
        ),
        job_application_email=(
            f"Subject: Application for {role}\n\nHi [hiring team],\n\nI am applying for the "
            f"{role} role at {company}. {intro} I have attached my resume for review.\n\nBest,\n"
            "[candidate name]"
        ),
        follow_up_email=(
            f"Hi [name],\n\nI wanted to follow up on my application for {role}. I remain "
            f"interested in {company} and would welcome the chance to discuss how my verified "
            f"background in {skill_text} may fit the team.\n\nBest,\n[candidate name]"
        ),
        interview_thank_you_email=(
            f"Hi [name],\n\nThank you for speaking with me about the {role} role. I appreciated "
            f"learning more about {company}. Our conversation reinforced my interest, especially "
            f"where my background in {skill_text} may be relevant.\n\nBest,\n[candidate name]"
        ),
        referral_request=(
            f"Hi [name], I am preparing to apply for {role} at {company}. Based on my verified "
            f"background in {skill_text}, would you be comfortable advising whether a referral "
            "request is appropriate?"
        ),
        short_professional_intro=intro,
        evidence_used=([skill_text] if skills else []) + experience[:2],
        missing_evidence_warnings=warnings,
        cautions=[
            "Review placeholders before sending.",
            "Do not add metrics, achievements, or responsibilities unless they are true.",
        ],
    )


def _skill_names(normalized_profile: dict[str, Any]) -> list[str]:
    skills = normalized_profile.get("skills")
    if not isinstance(skills, list):
        return []
    names = []
    for skill in skills:
        value = skill.get("name") if isinstance(skill, dict) else skill
        if isinstance(value, str) and value.strip():
            names.append(value.strip().lower())
    return sorted(set(names))[:20]


def _experience_signals(normalized_profile: dict[str, Any]) -> list[str]:
    sections = normalized_profile.get("sections")
    if not isinstance(sections, dict):
        return []
    text = sections.get("experience") or sections.get("projects") or sections.get("summary")
    if not isinstance(text, str):
        return []
    return [" ".join(text.split())[:220]] if text.strip() else []


def _job_summary(structured_job: dict[str, Any] | None) -> dict[str, Any] | None:
    if not structured_job:
        return None
    return {"title": structured_job.get("title"), "company": structured_job.get("company")}


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value.strip()]
