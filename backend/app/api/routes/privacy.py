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
    privacy_event_count: int = Field(ge=0)
    retention_policy: str


class DocumentDeletionResponse(BaseModel):
    profile_id: str
    deleted_storage_objects: int = Field(ge=0)
    profile_retained: bool


class PrivacyEventResponse(BaseModel):
    id: str | None = None
    event_type: str
    metadata: dict
    created_at: str | None = None


class ProfileDataExportResponse(BaseModel):
    profile_id: str
    export_version: str
    includes_raw_document_files: bool
    profile: dict
    sources: list[dict]
    evidence: list[dict]
    job_descriptions: list[dict]
    analyses: list[dict]
    generated_outputs: list[dict]
    privacy_events: list[PrivacyEventResponse]
    retention_policy: str


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
        events = supabase.list_privacy_events(user_id=user.id, profile_id=profile_id, limit=50)
        _record_privacy_event(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            event_type="privacy_summary_viewed",
            metadata={
                "stored_document_count": len(storage_paths),
                "generated_output_count": len(outputs),
            },
        )
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
        privacy_event_count=len(events),
        retention_policy=(
            "Raw uploaded documents are private; parsed profile facts and saved outputs "
            "remain until deleted."
        ),
    )


@router.get("/export", response_model=ProfileDataExportResponse)
def export_profile_data(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ProfileDataExportResponse:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        sources = supabase.list_profile_sources(profile_id=profile_id, user_id=user.id)
        evidence = supabase.list_profile_evidence(profile_id=profile_id)
        jobs = supabase.list_job_descriptions(profile_id=profile_id, user_id=user.id, limit=100)
        analyses = supabase.list_profile_analyses(user_id=user.id, profile_id=profile_id, limit=100)
        outputs = supabase.list_generated_outputs(user_id=user.id, profile_id=profile_id, limit=100)
        events = supabase.list_privacy_events(user_id=user.id, profile_id=profile_id, limit=100)
        _record_privacy_event(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            event_type="profile_data_exported",
            metadata={
                "source_count": len(sources),
                "evidence_count": len(evidence),
                "job_description_count": len(jobs),
                "analysis_count": len(analyses),
                "generated_output_count": len(outputs),
            },
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase {exc.operation} failed.",
        ) from exc

    return ProfileDataExportResponse(
        profile_id=profile_id,
        export_version="profile-data-export-v1",
        includes_raw_document_files=False,
        profile=profile,
        sources=sources,
        evidence=evidence,
        job_descriptions=[_without_raw_job_text(row) for row in jobs],
        analyses=analyses,
        generated_outputs=outputs,
        privacy_events=[PrivacyEventResponse(**event) for event in events],
        retention_policy=(
            "Export includes structured profile data, metadata, analyses, saved outputs, "
            "and audit events. Raw uploaded file bytes are not included."
        ),
    )


@router.get("/events", response_model=list[PrivacyEventResponse])
def list_privacy_events(
    profile_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> list[PrivacyEventResponse]:
    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        events = supabase.list_privacy_events(user_id=user.id, profile_id=profile_id, limit=50)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase {exc.operation} failed.",
        ) from exc
    return [PrivacyEventResponse(**event) for event in events]


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
        _record_privacy_event(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            event_type="profile_documents_deleted",
            metadata={"deleted_storage_objects": len(storage_paths)},
        )
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
        _record_privacy_event(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            event_type="profile_data_deletion_requested",
            metadata={
                "profile_id": profile_id,
                "deleted_storage_objects": len(storage_paths),
            },
        )
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


def _record_privacy_event(
    *,
    supabase: SupabaseClient,
    user_id: str,
    profile_id: str,
    event_type: str,
    metadata: dict,
) -> None:
    try:
        supabase.create_privacy_event(
            {
                "user_id": user_id,
                "profile_id": profile_id,
                "event_type": event_type,
                "metadata": metadata,
            }
        )
    except SupabaseError:
        return


def _without_raw_job_text(row: dict) -> dict:
    cleaned = dict(row)
    cleaned.pop("raw_text", None)
    return cleaned
