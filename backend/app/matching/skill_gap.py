import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

ANALYSIS_TYPE = "skill_gap"
DETERMINISTIC_VERSION = "skill-gap-matcher-v1"

SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "postgres": "sql",
    "postgresql": "sql",
    "sql": "sql",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "excel": "excel",
    "stakeholders": "stakeholder management",
    "stakeholder management": "stakeholder management",
    "project management": "project management",
    "program management": "project management",
}

TRANSFERABLE_SKILLS = {
    "communication",
    "leadership",
    "operations",
    "project management",
    "stakeholder management",
}


class SkillGapItem(BaseModel):
    skill: str
    category: str
    importance: str
    evidence: str | None = None


class SkillGapResult(BaseModel):
    analysis_type: str = ANALYSIS_TYPE
    deterministic_version: str = DETERMINISTIC_VERSION
    score: int = Field(ge=0, le=100)
    matched_skills: list[SkillGapItem] = Field(default_factory=list)
    partially_matched_skills: list[SkillGapItem] = Field(default_factory=list)
    missing_skills: list[SkillGapItem] = Field(default_factory=list)
    transferable_skills: list[SkillGapItem] = Field(default_factory=list)
    claimed_but_unverified_skills: list[SkillGapItem] = Field(default_factory=list)
    not_relevant_skills: list[SkillGapItem] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)


def analyze_skill_gap(
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any],
) -> SkillGapResult:
    candidate_skills = _profile_skills(normalized_profile)
    evidence_by_skill = _profile_skill_evidence(normalized_profile)
    required = _normalized_list(structured_job.get("required_skills"))
    preferred = _normalized_list(structured_job.get("preferred_skills"))
    tools = _normalized_list(structured_job.get("tools"))
    soft_skills = _normalized_list(structured_job.get("soft_skills"))
    job_skills = sorted(set(required + preferred + tools + soft_skills))

    matched = sorted(set(candidate_skills) & set(job_skills))
    missing_required = sorted(set(required) - set(candidate_skills))
    missing_preferred = sorted((set(preferred) | set(tools)) - set(candidate_skills))
    transferable = sorted(
        skill for skill in candidate_skills if skill in TRANSFERABLE_SKILLS and skill not in matched
    )
    not_relevant = sorted(set(candidate_skills) - set(job_skills) - set(transferable))
    unverified = sorted(skill for skill in matched if not evidence_by_skill.get(skill))

    partially_matched = _partial_matches(candidate_skills, job_skills, matched)
    partial_skill_names = {item[0] for item in partially_matched}
    missing = sorted(set(missing_required + missing_preferred) - partial_skill_names)
    score = _score(
        required=required,
        preferred=preferred,
        tools=tools,
        matched=matched,
        partial_count=len(partially_matched),
    )

    return SkillGapResult(
        score=score,
        matched_skills=[
            _item(skill, "matched", _importance(skill, required), evidence_by_skill.get(skill))
            for skill in matched
        ],
        partially_matched_skills=[
            _item(skill, "partially_matched", _importance(skill, required), evidence)
            for skill, evidence in partially_matched
        ],
        missing_skills=[
            _item(skill, "missing", _importance(skill, required), None)
            for skill in missing
        ],
        transferable_skills=[
            _item(skill, "transferable", "supporting", evidence_by_skill.get(skill))
            for skill in transferable
        ],
        claimed_but_unverified_skills=[
            _item(skill, "claimed_but_unverified", _importance(skill, required), None)
            for skill in unverified
        ],
        not_relevant_skills=[
            _item(skill, "not_relevant", "low", evidence_by_skill.get(skill))
            for skill in not_relevant
        ],
        checks={
            "has_candidate_skills": bool(candidate_skills),
            "has_job_skills": bool(job_skills),
            "has_required_skill_match": bool(set(candidate_skills) & set(required)),
        },
    )


def skill_gap_input_hash(normalized_profile: dict[str, Any], structured_job: dict[str, Any]) -> str:
    encoded = json.dumps(
        {"profile": normalized_profile, "job": structured_job},
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _profile_skills(normalized_profile: dict[str, Any]) -> list[str]:
    values = normalized_profile.get("skills")
    if not isinstance(values, list):
        return []
    skills = []
    for item in values:
        if isinstance(item, dict):
            value = item.get("name")
        else:
            value = item
        if isinstance(value, str) and value.strip():
            skills.append(_canonical(value))
    return sorted(set(skills))


def _profile_skill_evidence(normalized_profile: dict[str, Any]) -> dict[str, str]:
    values = normalized_profile.get("skills")
    if not isinstance(values, list):
        return {}
    evidence: dict[str, str] = {}
    for item in values:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        source = item.get("source")
        if isinstance(source, str) and source:
            evidence[_canonical(name)] = source
    return evidence


def _normalized_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(
        {_canonical(value) for value in values if isinstance(value, str) and value.strip()}
    )


def _canonical(value: str) -> str:
    normalized = " ".join(value.lower().strip().split())
    return SKILL_ALIASES.get(normalized, normalized)


def _partial_matches(
    candidate_skills: list[str],
    job_skills: list[str],
    matched: list[str],
) -> list[tuple[str, str | None]]:
    exact = set(matched)
    partial: list[tuple[str, str | None]] = []
    for job_skill in job_skills:
        if job_skill in exact:
            continue
        for candidate_skill in candidate_skills:
            if candidate_skill in exact:
                continue
            if job_skill in candidate_skill or candidate_skill in job_skill:
                partial.append((job_skill, f"Related profile skill: {candidate_skill}"))
                break
    return sorted(set(partial))


def _importance(skill: str, required: list[str]) -> str:
    return "high" if skill in required else "medium"


def _item(skill: str, category: str, importance: str, evidence: str | None) -> SkillGapItem:
    return SkillGapItem(skill=skill, category=category, importance=importance, evidence=evidence)


def _score(
    *,
    required: list[str],
    preferred: list[str],
    tools: list[str],
    matched: list[str],
    partial_count: int,
) -> int:
    weighted_total = len(required) * 3 + len(preferred) * 2 + len(tools)
    if weighted_total == 0:
        return 0
    matched_set = set(matched)
    weighted_match = (
        len(matched_set & set(required)) * 3
        + len(matched_set & set(preferred)) * 2
        + len(matched_set & set(tools))
        + partial_count
    )
    return min(100, round((weighted_match / weighted_total) * 100))
