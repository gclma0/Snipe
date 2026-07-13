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
