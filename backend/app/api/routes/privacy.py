from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/privacy", tags=["privacy"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


class ProfileDeletionResponse(BaseModel):
    profile_id: str
    deleted: bool
    deleted_storage_objects: int = Field(ge=0)


@router.delete("", response_model=ProfileDeletionResponse)
def delete_profile_data(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ProfileDeletionResponse:
    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        storage_paths = supabase.list_profile_storage_paths(profile_id=profile_id, user_id=user.id)
        supabase.delete_storage_objects(storage_paths)
        deleted = supabase.delete_candidate_profile(profile_id=profile_id, user_id=user.id)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase {exc.operation} failed.",
        ) from exc

    return ProfileDeletionResponse(
        profile_id=profile_id,
        deleted=deleted,
        deleted_storage_objects=len(storage_paths),
    )
