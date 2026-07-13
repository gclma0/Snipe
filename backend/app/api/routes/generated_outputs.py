from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/generated-outputs", tags=["generated-outputs"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


class GeneratedOutputResponse(BaseModel):
    id: str
    output_type: str
    job_description_id: str | None = None
    prompt_version: str | None = None
    provider: str | None = None
    model_name: str | None = None
    result_json: dict[str, Any]
    result_markdown: str | None = None
    status: str
    created_at: str | None = None


class GeneratedOutputDeletionResponse(BaseModel):
    output_id: str
    deleted: bool


@router.get("", response_model=list[GeneratedOutputResponse])
def list_generated_outputs(
    profile_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> list[GeneratedOutputResponse]:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        rows = supabase.list_generated_outputs(
            user_id=user.id,
            profile_id=profile_id,
            limit=limit,
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
    return [GeneratedOutputResponse(**row) for row in rows]


@router.get("/{output_id}", response_model=GeneratedOutputResponse)
def get_generated_output(
    profile_id: str,
    output_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> GeneratedOutputResponse:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        row = supabase.get_generated_output_by_id(
            user_id=user.id,
            profile_id=profile_id,
            output_id=output_id,
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated output not found.",
            )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
    return GeneratedOutputResponse(**row)


@router.delete("/{output_id}", response_model=GeneratedOutputDeletionResponse)
def delete_generated_output(
    profile_id: str,
    output_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> GeneratedOutputDeletionResponse:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        deleted = supabase.delete_generated_output(
            user_id=user.id,
            profile_id=profile_id,
            output_id=output_id,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generated output not found.",
            )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
    return GeneratedOutputDeletionResponse(output_id=output_id, deleted=True)
