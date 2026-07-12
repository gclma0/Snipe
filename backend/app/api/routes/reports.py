from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.reports.report_builder import (
    REPORT_TYPE,
    REPORT_VERSION,
    BasicReportResult,
    build_basic_report,
    report_input_hash,
)
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/reports", tags=["reports"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


class BasicReportRequest(BaseModel):
    job_description_id: str | None = None


@router.post("/basic", response_model=BasicReportResult, status_code=status.HTTP_201_CREATED)
def create_basic_report(
    profile_id: str,
    payload: BasicReportRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> BasicReportResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating a report.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = None
        if job_description_id:
            job_description = supabase.get_job_description(
                job_description_id=job_description_id,
                profile_id=profile_id,
                user_id=user.id,
            )
            if job_description is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job description not found.",
                )
            structured_job = job_description.get("structured_json") or {}

        result = build_basic_report(normalized_profile, structured_job)
        input_hash = report_input_hash(normalized_profile, structured_job)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": REPORT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": REPORT_VERSION,
                "provider": "deterministic",
                "model_name": "none",
                "result_json": result.model_dump(exclude={"markdown"}),
                "result_markdown": result.markdown,
                "status": "completed",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result
