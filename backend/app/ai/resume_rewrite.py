import json
import re
from hashlib import sha256
from typing import Any

from app.scoring.readiness import ReadinessDashboardResult

REWRITE_CONTEXT_VERSION = "ai-resume-rewrite-context-v1"


def build_resume_rewrite_context(
    *,
    normalized_profile: dict[str, Any],
    readiness: ReadinessDashboardResult,
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "context_version": REWRITE_CONTEXT_VERSION,
        "existing_bullets": _experience_bullets(normalized_profile),
        "verified_skills": _skill_names(normalized_profile),
        "target_job": _job_summary(structured_job),
        "skill_gap": _skill_gap_summary(readiness),
        "constraints": [
            "Rewrite only from existing bullets and verified skills.",
            "Do not invent metrics, achievements, employers, skills, or experience.",
            "Use placeholders only when the candidate must supply a real value.",
        ],
    }


def rewrite_context_hash(context: dict[str, Any]) -> str:
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _experience_bullets(normalized_profile: dict[str, Any]) -> list[str]:
    sections = normalized_profile.get("sections")
    if not isinstance(sections, dict):
        return []
    experience = str(sections.get("experience") or "")
    candidates = [
        re.sub(r"\s+", " ", line.strip(" -•\t")).strip()
        for line in experience.splitlines()
        if line.strip()
    ]
    if not candidates and experience:
        candidates = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", experience).strip())
    return [item[:240] for item in candidates if len(item) >= 20][:5]


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


def _skill_gap_summary(readiness: ReadinessDashboardResult) -> dict[str, Any] | None:
    if readiness.skill_gap is None:
        return None
    return {
        "matched": [item.skill for item in readiness.skill_gap.matched_skills[:10]],
        "missing": [item.skill for item in readiness.skill_gap.missing_skills[:10]],
        "transferable": [item.skill for item in readiness.skill_gap.transferable_skills[:8]],
    }


def _job_summary(structured_job: dict[str, Any] | None) -> dict[str, Any] | None:
    if not structured_job:
        return None
    return {
        "title": structured_job.get("title"),
        "required_skills": _list_from_dict(structured_job, "required_skills"),
        "preferred_skills": _list_from_dict(structured_job, "preferred_skills"),
        "ats_keywords": _list_from_dict(structured_job, "ats_keywords")[:20],
    }


def _list_from_dict(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    return value[:20] if isinstance(value, list) else []
