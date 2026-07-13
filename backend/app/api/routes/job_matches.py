import json
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.jobs.retrieval import retrieve_job_references
from app.matching.job_matcher import (
    ANALYSIS_TYPE,
    DETERMINISTIC_VERSION,
    JobMatchResult,
    build_job_match_query,
    match_jobs_from_rag,
)
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/job-matches", tags=["job matches"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


class JobMatchRequest(BaseModel):
    query: str | None = Field(default=None, min_length=2, max_length=1000)
    limit: int = Field(default=10, ge=1, le=20)


class SavedJobMatchRun(BaseModel):
    id: str
    analysis_type: str
    query: str
    match_count: int
    top_match_title: str | None = None
    top_match_score: int | None = None
    created_at: str | None = None
    result: JobMatchResult


@router.post("", response_model=JobMatchResult, status_code=status.HTTP_201_CREATED)
def create_job_matches(
    profile_id: str,
    payload: JobMatchRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> JobMatchResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before running job matches.",
            )

        query = build_job_match_query(
            normalized_profile,
            fallback=(payload.query if payload else None) or profile.get("preferred_role"),
        )
        rag_result = retrieve_job_references(
            query=query,
            user_id=user.id,
            supabase=supabase,
            limit=payload.limit if payload else 10,
        )
        result = match_jobs_from_rag(
            normalized_profile=normalized_profile,
            rag_result=rag_result,
            query=query,
        )
        supabase.create_analysis(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "analysis_type": ANALYSIS_TYPE,
                "input_hash": _job_match_input_hash(
                    normalized_profile=normalized_profile,
                    query=query,
                    job_reference_ids=[match.job_reference_id for match in result.matches],
                ),
                "profile_version": profile.get("version") or 1,
                "deterministic_version": DETERMINISTIC_VERSION,
                "result_json": result.model_dump(),
                "score": result.matches[0].match_score if result.matches else 0,
                "status": "completed",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result


@router.get("", response_model=list[SavedJobMatchRun])
def list_job_match_runs(
    profile_id: str,
    limit: int = 20,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> list[SavedJobMatchRun]:
    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        rows = supabase.list_analyses(
            user_id=user.id,
            profile_id=profile_id,
            analysis_type=ANALYSIS_TYPE,
            limit=max(1, min(limit, 50)),
        )
        return [_saved_run_from_row(row) for row in rows]
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.get("/{analysis_id}", response_model=SavedJobMatchRun)
def get_job_match_run(
    profile_id: str,
    analysis_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> SavedJobMatchRun:
    try:
        row = supabase.get_analysis(
            user_id=user.id,
            profile_id=profile_id,
            analysis_id=analysis_id,
            analysis_type=ANALYSIS_TYPE,
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job match run not found.",
            )
        return _saved_run_from_row(row)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


def _saved_run_from_row(row: dict) -> SavedJobMatchRun:
    result = JobMatchResult(**(row.get("result_json") or {}))
    top_match = result.matches[0] if result.matches else None
    return SavedJobMatchRun(
        id=row["id"],
        analysis_type=row.get("analysis_type") or ANALYSIS_TYPE,
        query=result.query,
        match_count=result.match_count,
        top_match_title=top_match.title if top_match else None,
        top_match_score=top_match.match_score if top_match else None,
        created_at=row.get("created_at"),
        result=result,
    )


def _job_match_input_hash(
    *,
    normalized_profile: dict,
    query: str,
    job_reference_ids: list[str],
) -> str:
    encoded = json.dumps(
        {
            "profile": normalized_profile,
            "query": query,
            "job_reference_ids": job_reference_ids,
            "version": DETERMINISTIC_VERSION,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()
