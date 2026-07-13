import json
from hashlib import sha256
from typing import Any

from app.scoring.readiness import ReadinessDashboardResult

TAILORING_CONTEXT_VERSION = "ai-resume-tailoring-context-v1"


def build_resume_tailoring_context(
    *,
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    skills = _skill_names(normalized_profile)
    return {
        "context_version": TAILORING_CONTEXT_VERSION,
        "verified_skills": skills,
        "profile_summary_present": _has_summary(normalized_profile),
        "target_job": _job_summary(structured_job),
        "skill_gap": _skill_gap_summary(readiness),
        "readiness": {
            "overall": readiness.scores.overall,
            "ats_readiness": readiness.scores.ats_readiness,
            "skill_alignment": readiness.scores.skill_alignment,
            "profile_completeness": readiness.scores.profile_completeness,
        },
        "constraints": [
            "Use only verified skills and compact job requirements.",
            "Recommend keyword placement, not fabricated claims.",
            "Warn when missing keywords have no supporting evidence.",
            "Do not invent achievements, metrics, skills, employers, or experience.",
        ],
    }


def tailoring_context_hash(context: dict[str, Any]) -> str:
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _skill_names(normalized_profile: dict[str, Any]) -> list[str]:
    skills = normalized_profile.get("skills")
    names: set[str] = set()
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, dict) and isinstance(skill.get("name"), str):
                names.add(skill["name"].strip().lower())
            elif isinstance(skill, str):
                names.add(skill.strip().lower())
    return sorted(name for name in names if name)[:30]


def _has_summary(normalized_profile: dict[str, Any]) -> bool:
    sections = normalized_profile.get("sections")
    return isinstance(sections, dict) and bool(str(sections.get("summary") or "").strip())


def _skill_gap_summary(readiness: ReadinessDashboardResult) -> dict[str, Any] | None:
    if readiness.skill_gap is None:
        return None
    return {
        "matched": [item.skill for item in readiness.skill_gap.matched_skills[:12]],
        "partially_matched": [
            item.skill for item in readiness.skill_gap.partially_matched_skills[:8]
        ],
        "missing": [item.skill for item in readiness.skill_gap.missing_skills[:12]],
        "transferable": [item.skill for item in readiness.skill_gap.transferable_skills[:8]],
    }


def _job_summary(structured_job: dict[str, Any] | None) -> dict[str, Any] | None:
    if not structured_job:
        return None
    return {
        "title": structured_job.get("title"),
        "seniority": structured_job.get("seniority"),
        "required_skills": _list_from_dict(structured_job, "required_skills"),
        "preferred_skills": _list_from_dict(structured_job, "preferred_skills"),
        "tools": _list_from_dict(structured_job, "tools"),
        "soft_skills": _list_from_dict(structured_job, "soft_skills"),
        "ats_keywords": _list_from_dict(structured_job, "ats_keywords")[:20],
    }


def _list_from_dict(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    return value[:20] if isinstance(value, list) else []
