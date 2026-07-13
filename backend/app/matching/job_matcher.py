from typing import Any, Literal

from pydantic import BaseModel, Field

from app.jobs.job_parser import parse_job_description
from app.matching.skill_gap import SkillGapResult, analyze_skill_gap
from app.rag.schemas import RagCitation, RagSearchResult

ANALYSIS_TYPE = "job_match"
DETERMINISTIC_VERSION = "deterministic-job-matcher-v1"


class JobMatchCitation(BaseModel):
    document_id: str
    chunk_id: str | None = None
    title: str
    source_type: str
    source_url: str | None = None
    score: float = Field(ge=0, le=1)


class JobMatch(BaseModel):
    job_reference_id: str
    title: str
    company: str | None = None
    match_score: int = Field(ge=0, le=100)
    semantic_score: float = Field(ge=0, le=1)
    skill_alignment_score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    partially_matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    relevant_experience: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    explanation: str
    apply_recommendation: Literal["strong_apply", "apply_with_tailoring", "build_evidence_first"]
    citation: JobMatchCitation


class JobMatchResult(BaseModel):
    analysis_type: str = ANALYSIS_TYPE
    deterministic_version: str = DETERMINISTIC_VERSION
    query: str
    match_count: int
    matches: list[JobMatch]
    checks: dict[str, bool] = Field(default_factory=dict)


def match_jobs_from_rag(
    *,
    normalized_profile: dict[str, Any],
    rag_result: RagSearchResult,
    query: str,
) -> JobMatchResult:
    matches = [
        _match_citation(normalized_profile=normalized_profile, citation=citation)
        for citation in rag_result.citations
    ]
    matches.sort(key=lambda item: item.match_score, reverse=True)
    return JobMatchResult(
        query=query,
        match_count=len(matches),
        matches=matches,
        checks={
            "has_candidate_profile": bool(normalized_profile),
            "has_retrieved_jobs": bool(rag_result.citations),
            "uses_deterministic_ranking": True,
            "uses_source_citations": all(bool(match.citation.document_id) for match in matches),
        },
    )


def build_job_match_query(normalized_profile: dict[str, Any], fallback: str | None = None) -> str:
    values: list[str] = []
    if fallback:
        values.append(fallback)
    sections = normalized_profile.get("sections")
    if isinstance(sections, dict):
        for key in ("summary", "experience", "projects"):
            value = sections.get(key)
            if isinstance(value, str) and value.strip():
                values.append(value[:400])
    skills = normalized_profile.get("skills")
    if isinstance(skills, list):
        skill_names = [
            item.get("name") if isinstance(item, dict) else item
            for item in skills
        ]
        values.extend(value for value in skill_names if isinstance(value, str))
    query = " ".join(values)
    return query[:1000] if query else "career role job listing"


def _match_citation(*, normalized_profile: dict[str, Any], citation: RagCitation) -> JobMatch:
    structured_job = parse_job_description(citation.content).model_dump()
    if not structured_job.get("title"):
        structured_job["title"] = citation.title
    skill_gap = analyze_skill_gap(normalized_profile, structured_job)
    match_score = _combined_score(skill_gap=skill_gap, semantic_score=citation.score)
    matched = [item.skill for item in skill_gap.matched_skills]
    partially_matched = [item.skill for item in skill_gap.partially_matched_skills]
    missing = [item.skill for item in skill_gap.missing_skills]
    relevant_experience = _relevant_experience(normalized_profile, matched + partially_matched)
    concerns = _concerns(skill_gap, relevant_experience)
    return JobMatch(
        job_reference_id=citation.document_id,
        title=structured_job.get("title") or citation.title,
        company=structured_job.get("company"),
        match_score=match_score,
        semantic_score=citation.score,
        skill_alignment_score=skill_gap.score,
        matched_skills=matched,
        partially_matched_skills=partially_matched,
        missing_skills=missing,
        relevant_experience=relevant_experience,
        concerns=concerns,
        explanation=_explanation(match_score, matched, missing, citation.title),
        apply_recommendation=_apply_recommendation(match_score, missing),
        citation=JobMatchCitation(
            document_id=citation.document_id,
            chunk_id=citation.chunk_id,
            title=citation.title,
            source_type=citation.source_type,
            source_url=citation.source_url,
            score=citation.score,
        ),
    )


def _combined_score(*, skill_gap: SkillGapResult, semantic_score: float) -> int:
    semantic_component = round(max(0.0, min(1.0, semantic_score)) * 100)
    return round((skill_gap.score * 0.75) + (semantic_component * 0.25))


def _relevant_experience(normalized_profile: dict[str, Any], skills: list[str]) -> list[str]:
    sections = normalized_profile.get("sections")
    if not isinstance(sections, dict):
        return []
    experience = sections.get("experience") or sections.get("projects") or sections.get("summary")
    if not isinstance(experience, str) or not experience.strip():
        return []
    lowered = experience.lower()
    snippets = []
    for skill in skills:
        if skill.lower() in lowered:
            snippets.append(f"Profile evidence mentions {skill}: {experience[:220]}")
    return snippets[:3]


def _concerns(skill_gap: SkillGapResult, relevant_experience: list[str]) -> list[str]:
    concerns = []
    missing_required = [
        item.skill for item in skill_gap.missing_skills if item.importance == "high"
    ]
    if missing_required:
        concerns.append(f"Missing required skills: {', '.join(missing_required[:5])}.")
    if skill_gap.claimed_but_unverified_skills:
        concerns.append("Some matched skills do not have strong evidence in the profile.")
    if not relevant_experience:
        concerns.append("No directly relevant experience excerpt was found in the profile.")
    return concerns


def _explanation(match_score: int, matched: list[str], missing: list[str], title: str) -> str:
    matched_text = ", ".join(matched[:5]) if matched else "no verified skill matches"
    missing_text = ", ".join(missing[:5]) if missing else "no major parsed skill gaps"
    return (
        f"{title} scored {match_score} because the profile matches {matched_text}; "
        f"remaining gaps include {missing_text}."
    )


def _apply_recommendation(
    match_score: int,
    missing_skills: list[str],
) -> Literal["strong_apply", "apply_with_tailoring", "build_evidence_first"]:
    if match_score >= 75 and len(missing_skills) <= 2:
        return "strong_apply"
    if match_score >= 45:
        return "apply_with_tailoring"
    return "build_evidence_first"
