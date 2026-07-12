from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles", tags=["profiles"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


class CandidateProfileCreate(BaseModel):
    career_goal: str = Field(min_length=1, max_length=120)
    preferred_role: str = Field(min_length=1, max_length=120)


class CandidateProfileResponse(BaseModel):
    id: str
    career_goal: str | None = None
    preferred_role: str | None = None
    profile_status: str


@router.get("", response_model=list[CandidateProfileResponse])
def list_profiles(
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> list[CandidateProfileResponse]:
    try:
        rows = supabase.list_candidate_profiles(user.id)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
    return [CandidateProfileResponse(**row) for row in rows]


@router.post("", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: CandidateProfileCreate,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> CandidateProfileResponse:
    try:
        row = supabase.create_candidate_profile(
            {
                "user_id": user.id,
                "career_goal": payload.career_goal,
                "preferred_role": payload.preferred_role,
                "profile_status": "draft",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
    return CandidateProfileResponse(**row)
