import json
import re
from hashlib import sha256
from typing import Any

from app.scoring.readiness import ReadinessDashboardResult

INTERVIEW_CONTEXT_VERSION = "ai-interview-prep-context-v1"


def build_interview_prep_context(
    *,
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "context_version": INTERVIEW_CONTEXT_VERSION,
        "verified_skills": _skill_names(normalized_profile),
        "experience_signals": _experience_signals(normalized_profile),
        "target_job": _job_summary(structured_job),
        "skill_gap": _skill_gap_summary(readiness),
        "readiness": {
            "overall": readiness.scores.overall,
            "skill_alignment": readiness.scores.skill_alignment,
            "primary_specialization": (
                readiness.interpretation.primary_specialization.name
                if readiness.interpretation.primary_specialization
                else None
            ),
            "estimated_seniority": readiness.interpretation.estimated_seniority,
        },
        "constraints": [
            "Use only verified skills, short experience signals, and compact job requirements.",
            "Create practice guidance, not finished answers with fabricated claims.",
            "Warn when a question needs evidence that is missing from the profile.",
            "Do not invent achievements, metrics, skills, employers, credentials, or experience.",
        ],
    }


def interview_context_hash(context: dict[str, Any]) -> str:
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


def _experience_signals(normalized_profile: dict[str, Any]) -> list[str]:
    sections = normalized_profile.get("sections")
    if not isinstance(sections, dict):
        return []
    experience = sections.get("experience")
    if not isinstance(experience, str):
        return []
    signals: list[str] = []
    for part in re.split(r"[\n.;]+", experience):
        cleaned = " ".join(part.strip(" -\t\r").split())
        if len(cleaned) < 12:
            continue
        signals.append(cleaned[:220])
        if len(signals) >= 5:
            break
    return signals


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
        "responsibilities": _list_from_dict(structured_job, "responsibilities")[:8],
        "ats_keywords": _list_from_dict(structured_job, "ats_keywords")[:20],
    }


def _list_from_dict(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    return value[:20] if isinstance(value, list) else []
