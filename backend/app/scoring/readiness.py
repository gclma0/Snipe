from typing import Any

from pydantic import BaseModel, Field

from app.ai.profile_interpreter import ProfileInterpretationResult, interpret_profile
from app.analysis.resume_quality import analyze_resume_quality
from app.matching.skill_gap import SkillGapResult, analyze_skill_gap
from app.scoring.ats import analyze_ats_readiness
from app.scoring.profile_completeness import analyze_profile_completeness

ANALYSIS_TYPE = "readiness_dashboard"
DETERMINISTIC_VERSION = "readiness-dashboard-v1"


class ReadinessScores(BaseModel):
    overall: int = Field(ge=0, le=100)
    resume_quality: int = Field(ge=0, le=100)
    ats_readiness: int = Field(ge=0, le=100)
    skill_alignment: int | None = Field(default=None, ge=0, le=100)
    profile_completeness: int = Field(ge=0, le=100)


class ReadinessDashboardResult(BaseModel):
    analysis_type: str = ANALYSIS_TYPE
    deterministic_version: str = DETERMINISTIC_VERSION
    scores: ReadinessScores
    interpretation: ProfileInterpretationResult
    skill_gap: SkillGapResult | None = None
    checks: dict[str, bool] = Field(default_factory=dict)


def build_readiness_dashboard(
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any] | None = None,
) -> ReadinessDashboardResult:
    resume_quality = analyze_resume_quality(normalized_profile)
    ats_readiness = analyze_ats_readiness(normalized_profile)
    completeness = analyze_profile_completeness(normalized_profile)
    skill_gap = analyze_skill_gap(normalized_profile, structured_job) if structured_job else None
    scores = _scores(
        resume_quality=resume_quality.score,
        ats_readiness=ats_readiness.score,
        profile_completeness=completeness.score,
        skill_alignment=skill_gap.score if skill_gap else None,
    )
    return ReadinessDashboardResult(
        scores=scores,
        interpretation=interpret_profile(normalized_profile),
        skill_gap=skill_gap,
        checks={
            "has_profile": bool(normalized_profile),
            "has_target_job": structured_job is not None,
            "has_skill_alignment": skill_gap is not None,
        },
    )


def _scores(
    *,
    resume_quality: int,
    ats_readiness: int,
    profile_completeness: int,
    skill_alignment: int | None,
) -> ReadinessScores:
    weighted = resume_quality * 0.3 + ats_readiness * 0.25 + profile_completeness * 0.25
    if skill_alignment is None:
        overall = round(weighted / 0.8)
    else:
        overall = round(weighted + skill_alignment * 0.2)
    return ReadinessScores(
        overall=max(0, min(100, overall)),
        resume_quality=resume_quality,
        ats_readiness=ats_readiness,
        profile_completeness=profile_completeness,
        skill_alignment=skill_alignment,
    )
