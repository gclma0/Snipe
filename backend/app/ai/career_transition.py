import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from app.scoring.readiness import ReadinessDashboardResult

CAREER_TRANSITION_VERSION = "deterministic-career-transition-v1"
CAREER_TRANSITION_CONTEXT_VERSION = "deterministic-career-transition-context-v1"


class CareerTransitionResult(BaseModel):
    output_type: str = "ai_career_transition_analysis"
    output_version: str = CAREER_TRANSITION_VERSION
    provider: str = "deterministic"
    model_name: str = "deterministic-career-transition-v1"
    summary: str
    transferable_skills: list[str] = Field(default_factory=list, max_length=10)
    reframed_experience: list[str] = Field(default_factory=list, max_length=6)
    missing_foundational_knowledge: list[str] = Field(default_factory=list, max_length=10)
    transitional_roles: list[str] = Field(default_factory=list, max_length=8)
    recommended_projects: list[str] = Field(default_factory=list, max_length=6)
    learning_sequence: list[str] = Field(default_factory=list, max_length=8)
    resume_positioning: list[str] = Field(default_factory=list, max_length=6)
    likely_interview_concerns: list[str] = Field(default_factory=list, max_length=6)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


def build_career_transition_context(
    *,
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "context_version": CAREER_TRANSITION_CONTEXT_VERSION,
        "verified_skills": _skill_names(normalized_profile),
        "experience_signals": _experience_signals(normalized_profile),
        "target_job": _job_summary(structured_job),
        "skill_gap": _skill_gap_summary(readiness),
        "readiness": {
            "primary_specialization": (
                readiness.interpretation.primary_specialization.name
                if readiness.interpretation.primary_specialization
                else None
            ),
            "estimated_seniority": readiness.interpretation.estimated_seniority,
        },
    }


def career_transition_context_hash(context: dict[str, Any]) -> str:
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def generate_career_transition_analysis(context: dict[str, Any]) -> CareerTransitionResult:
    skills = _string_list(context.get("verified_skills"))
    experience = _string_list(context.get("experience_signals"))
    target_job = context.get("target_job") if isinstance(context.get("target_job"), dict) else {}
    skill_gap = context.get("skill_gap") if isinstance(context.get("skill_gap"), dict) else {}
    missing = _string_list(skill_gap.get("missing"))
    transferable = _transition_skills(skills)
    role = str(target_job.get("title") or "the target role")
    return CareerTransitionResult(
        summary=f"Career transition analysis for {role} based on verified profile evidence.",
        transferable_skills=transferable,
        reframed_experience=[
            f"Position this verified experience for {role}: {item}" for item in experience[:3]
        ],
        missing_foundational_knowledge=missing[:8]
        or ["Add target-job requirements to identify missing foundations."],
        transitional_roles=_transitional_roles(role, transferable),
        recommended_projects=[
            f"Build a focused portfolio proof using {skill} for a realistic {role} task."
            for skill in (transferable[:3] or skills[:3])
        ],
        learning_sequence=[
            "Confirm target-role requirements from real job descriptions.",
            "Close the highest-priority missing foundation first.",
            "Build one small project that demonstrates verified transferable skills.",
            "Update resume positioning with true project or work evidence.",
            "Practice interview answers around gaps and transition rationale.",
        ],
        resume_positioning=[
            "Lead with verified transferable skills instead of unsupported target-role claims.",
            "Use a career-transition summary that states direction and evidence honestly.",
            "Add recommended projects only after they are actually completed.",
        ],
        likely_interview_concerns=[
            f"Why are you moving into {role}?",
            "Which skills are already proven, and which are still developing?",
            "What evidence shows you can perform target-role tasks?",
            "How will you close gaps without overstating experience?",
        ],
        cautions=[
            "Do not present recommended projects or learning goals as completed work.",
            "Do not claim target-role experience until real evidence exists.",
        ],
    )


def _transition_skills(skills: list[str]) -> list[str]:
    transferable_terms = {
        "communication",
        "customer service",
        "documentation",
        "excel",
        "google sheets",
        "leadership",
        "microsoft office",
        "project management",
        "sql",
        "stakeholder management",
    }
    matched = [skill for skill in skills if skill in transferable_terms]
    return matched or skills[:5]


def _transitional_roles(role: str, transferable: list[str]) -> list[str]:
    base = role.lower()
    if "data" in base or "analyst" in base:
        return [
            "Reporting Analyst",
            "Operations Analyst",
            "Junior Data Analyst",
            "Business Analyst",
        ]
    if "software" in base or "developer" in base or "engineer" in base:
        return [
            "QA Analyst",
            "Technical Support Specialist",
            "Junior Developer",
            "Automation Tester",
        ]
    if "marketing" in base:
        return ["Marketing Coordinator", "CRM Coordinator", "Content Analyst", "Campaign Assistant"]
    return [
        "Coordinator role",
        "Assistant role",
        "Junior specialist role",
        "Operations support role",
    ]


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
    if not isinstance(text, str) or not text.strip():
        return []
    return [" ".join(text.split())[:220]]


def _skill_gap_summary(readiness: ReadinessDashboardResult) -> dict[str, Any] | None:
    if readiness.skill_gap is None:
        return None
    return {
        "missing": [item.skill for item in readiness.skill_gap.missing_skills[:12]],
        "transferable": [item.skill for item in readiness.skill_gap.transferable_skills[:8]],
    }


def _job_summary(structured_job: dict[str, Any] | None) -> dict[str, Any] | None:
    if not structured_job:
        return None
    return {
        "title": structured_job.get("title"),
        "required_skills": structured_job.get("required_skills"),
    }


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value.strip()]
