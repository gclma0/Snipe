from fastapi import APIRouter, Depends, HTTPException, status

from app.analysis.resume_quality import (
    ANALYSIS_TYPE,
    DETERMINISTIC_VERSION,
    ResumeQualityResult,
    analysis_input_hash,
    analyze_resume_quality,
)
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.scoring.ats import (
    ANALYSIS_TYPE as ATS_ANALYSIS_TYPE,
)
from app.scoring.ats import (
    DETERMINISTIC_VERSION as ATS_DETERMINISTIC_VERSION,
)
from app.scoring.ats import (
    analyze_ats_readiness,
)
from app.scoring.common import DeterministicScoreResult, normalized_profile_hash
from app.scoring.profile_completeness import (
    ANALYSIS_TYPE as COMPLETENESS_ANALYSIS_TYPE,
)
from app.scoring.profile_completeness import (
    DETERMINISTIC_VERSION as COMPLETENESS_DETERMINISTIC_VERSION,
)
from app.scoring.profile_completeness import (
    analyze_profile_completeness,
)
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/analyses", tags=["analyses"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


@router.post(
    "/resume-quality",
    response_model=ResumeQualityResult,
    status_code=status.HTTP_201_CREATED,
)
def create_resume_quality_analysis(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ResumeQualityResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before running resume quality analysis.",
            )

        result = analyze_resume_quality(normalized_profile)
        supabase.create_analysis(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "analysis_type": ANALYSIS_TYPE,
                "input_hash": analysis_input_hash(normalized_profile),
                "profile_version": profile.get("version") or 1,
                "deterministic_version": DETERMINISTIC_VERSION,
                "result_json": result.model_dump(),
                "score": result.score,
                "status": "completed",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result


@router.post(
    "/ats-readiness",
    response_model=DeterministicScoreResult,
    status_code=status.HTTP_201_CREATED,
)
def create_ats_readiness_analysis(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> DeterministicScoreResult:
    return _create_score_analysis(
        profile_id=profile_id,
        user=user,
        supabase=supabase,
        analysis_type=ATS_ANALYSIS_TYPE,
        deterministic_version=ATS_DETERMINISTIC_VERSION,
        analyzer=analyze_ats_readiness,
    )


@router.post(
    "/profile-completeness",
    response_model=DeterministicScoreResult,
    status_code=status.HTTP_201_CREATED,
)
def create_profile_completeness_analysis(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> DeterministicScoreResult:
    return _create_score_analysis(
        profile_id=profile_id,
        user=user,
        supabase=supabase,
        analysis_type=COMPLETENESS_ANALYSIS_TYPE,
        deterministic_version=COMPLETENESS_DETERMINISTIC_VERSION,
        analyzer=analyze_profile_completeness,
    )


def _create_score_analysis(
    *,
    profile_id: str,
    user: AuthenticatedUser,
    supabase: SupabaseClient,
    analysis_type: str,
    deterministic_version: str,
    analyzer,
) -> DeterministicScoreResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before running this analysis.",
            )

        result = analyzer(normalized_profile)
        supabase.create_analysis(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "analysis_type": analysis_type,
                "input_hash": normalized_profile_hash(normalized_profile),
                "profile_version": profile.get("version") or 1,
                "deterministic_version": deterministic_version,
                "result_json": result.model_dump(),
                "score": result.score,
                "status": "completed",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result
