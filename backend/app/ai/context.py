import json
from hashlib import sha256
from typing import Any

from app.scoring.readiness import ReadinessDashboardResult

CONTEXT_VERSION = "ai-compact-context-v1"


def build_ai_interpretation_context(
    *,
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    optional_sources = normalized_profile.get("optional_sources") or {}
    return {
        "context_version": CONTEXT_VERSION,
        "skills": _skill_names(normalized_profile),
        "source_summary": {
            "has_resume": bool(normalized_profile.get("sources")),
            "has_github": "github" in optional_sources,
            "has_portfolio": "portfolio" in optional_sources,
            "has_linkedin": "linkedin" in optional_sources,
        },
        "optional_sources": _optional_source_summary(optional_sources),
        "readiness": {
            "overall": readiness.scores.overall,
            "resume_quality": readiness.scores.resume_quality,
            "ats_readiness": readiness.scores.ats_readiness,
            "skill_alignment": readiness.scores.skill_alignment,
            "profile_completeness": readiness.scores.profile_completeness,
            "primary_specialization": (
                readiness.interpretation.primary_specialization.name
                if readiness.interpretation.primary_specialization
                else None
            ),
            "estimated_seniority": readiness.interpretation.estimated_seniority,
        },
        "skill_gap": _skill_gap_summary(readiness),
        "target_job": _job_summary(structured_job),
    }


def ai_context_hash(context: dict[str, Any]) -> str:
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


def _optional_source_summary(optional_sources: dict[str, Any]) -> dict[str, Any]:
    github = optional_sources.get("github") if isinstance(optional_sources, dict) else None
    portfolio = optional_sources.get("portfolio") if isinstance(optional_sources, dict) else None
    linkedin = optional_sources.get("linkedin") if isinstance(optional_sources, dict) else None
    return {
        "github": {
            "primary_languages": _list_value(github, "primary_languages"),
            "repository_count": _value(github, "analyzed_repository_count"),
            "testing_signals": _value(github, "test_signal_count"),
            "ci_signals": _value(github, "ci_signal_count"),
        },
        "portfolio": {
            "technical_signals": _list_value(portfolio, "technical_signals"),
            "non_technical_signals": _list_value(portfolio, "non_technical_signals"),
            "project_signal_count": _value(portfolio, "project_signal_count"),
            "contact_signal_count": _value(portfolio, "contact_signal_count"),
        },
        "linkedin": {
            "headline_present": bool(_value(linkedin, "headline")),
            "skill_signals": _list_value(linkedin, "skill_signals"),
            "experience_count": len(_list_value(linkedin, "experience_items")),
        },
    }


def _skill_gap_summary(readiness: ReadinessDashboardResult) -> dict[str, Any] | None:
    if readiness.skill_gap is None:
        return None
    return {
        "score": readiness.skill_gap.score,
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


def _value(data: Any, key: str) -> Any:
    return data.get(key) if isinstance(data, dict) else None


def _list_value(data: Any, key: str) -> list[Any]:
    value = _value(data, key)
    return value[:20] if isinstance(value, list) else []


def _list_from_dict(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    return value[:20] if isinstance(value, list) else []
