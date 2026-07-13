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


class PrivacyDataSummaryResponse(BaseModel):
    profile_id: str
    profile_exists: bool
    stored_document_count: int = Field(ge=0)
    generated_output_count: int = Field(ge=0)
    retention_policy: str


class DocumentDeletionResponse(BaseModel):
    profile_id: str
    deleted_storage_objects: int = Field(ge=0)
    profile_retained: bool


@router.get("/data-summary", response_model=PrivacyDataSummaryResponse)
def get_privacy_data_summary(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> PrivacyDataSummaryResponse:
    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        storage_paths = supabase.list_profile_storage_paths(profile_id=profile_id, user_id=user.id)
        outputs = supabase.list_generated_outputs(user_id=user.id, profile_id=profile_id, limit=50)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase {exc.operation} failed.",
        ) from exc

    return PrivacyDataSummaryResponse(
        profile_id=profile_id,
        profile_exists=True,
        stored_document_count=len(storage_paths),
        generated_output_count=len(outputs),
        retention_policy=(
            "Raw uploaded documents are private; parsed profile facts and saved outputs "
            "remain until deleted."
        ),
    )


@router.delete("/documents", response_model=DocumentDeletionResponse)
def delete_profile_documents(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> DocumentDeletionResponse:
    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        storage_paths = supabase.list_profile_storage_paths(profile_id=profile_id, user_id=user.id)
        supabase.delete_storage_objects(storage_paths)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase {exc.operation} failed.",
        ) from exc

    return DocumentDeletionResponse(
        profile_id=profile_id,
        deleted_storage_objects=len(storage_paths),
        profile_retained=True,
    )


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
