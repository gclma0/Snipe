from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.analysis.linkedin import analyze_linkedin_profile, linkedin_evidence
from app.api.routes.source_common import (
    MAX_RESUME_BYTES,
    CurrentUser,
    Supabase,
    create_evidence,
    update_optional_source,
)
from app.auth.dependencies import AuthenticatedUser
from app.parsing.linkedin_parser import LinkedInParseError, LinkedInParseResult, parse_linkedin_text
from app.parsing.resume_parser import SUPPORTED_RESUME_EXTENSIONS, parse_resume, resume_extension
from app.storage.paths import candidate_document_path
from app.supabase.client import SupabaseClient, SupabaseError

router = APIRouter()


class LinkedInTextSourceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=60000)


class LinkedInSourceResponse(BaseModel):
    source_id: str | None = None
    profile_id: str
    source_type: str
    status: str
    headline: str | None = None
    skill_signals: list[str]
    experience_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    profile_version: int | None = Field(default=None, ge=1)
    delete_after_parsing: bool = False
    raw_document_retained: bool = True


@router.post(
    "/linkedin",
    response_model=LinkedInSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_linkedin_text_source(
    profile_id: str,
    payload: LinkedInTextSourceRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> LinkedInSourceResponse:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        parsed = parse_linkedin_text(payload.text)
        return _save_linkedin_source(
            profile_id=profile_id,
            user_id=user.id,
            profile=profile,
            supabase=supabase,
            parsed=parsed,
            original_filename="linkedin-pasted-text",
        )
    except LinkedInParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.post(
    "/linkedin/upload",
    response_model=LinkedInSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_linkedin_source(
    profile_id: str,
    file: Annotated[UploadFile, File(...)],
    delete_after_parsing: Annotated[bool, Form()] = False,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> LinkedInSourceResponse:
    filename = file.filename or ""
    extension = resume_extension(filename)
    if extension not in SUPPORTED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="LinkedIn upload must be a PDF or DOCX file.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn file is empty.",
        )
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="LinkedIn file must be 8 MB or smaller.",
        )

    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        parsed_document = parse_resume(filename, content)
        linkedin_source_type = f"linkedin_{extension.lstrip('.')}"
        parsed = parse_linkedin_text(parsed_document.text, source_type=linkedin_source_type)
        storage_path = candidate_document_path(user.id, profile_id, f"linkedin-{filename}")
        supabase.upload_document(
            path=storage_path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        return _save_linkedin_source(
            profile_id=profile_id,
            user_id=user.id,
            profile=profile,
            supabase=supabase,
            parsed=parsed,
            original_filename=filename,
            storage_path=storage_path,
            content_hash=sha256(content).hexdigest(),
            delete_after_parsing=delete_after_parsing,
        )
    except LinkedInParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


def _save_linkedin_source(
    *,
    profile_id: str,
    user_id: str,
    profile: dict[str, Any],
    supabase: SupabaseClient,
    parsed: LinkedInParseResult,
    original_filename: str,
    storage_path: str | None = None,
    content_hash: str | None = None,
    delete_after_parsing: bool = False,
) -> LinkedInSourceResponse:
    text_hash = sha256(parsed.text.encode("utf-8")).hexdigest()
    source = supabase.create_profile_source(
        {
            "profile_id": profile_id,
            "user_id": user_id,
            "source_type": parsed.source_type,
            "storage_path": storage_path,
            "original_filename": original_filename,
            "content_hash": content_hash or text_hash,
            "parsed_text_hash": text_hash,
            "parser_version": parsed.parser,
            "status": "analyzed",
            "delete_after_parsing": delete_after_parsing,
            "retention_policy": (
                "delete_after_parsing" if delete_after_parsing else "retain_private"
            ),
            "parsed_at": datetime.now(tz=UTC).isoformat(),
        }
    )
    source_id = source.get("id")
    raw_document_retained = bool(storage_path)
    if delete_after_parsing and storage_path:
        supabase.delete_storage_objects([storage_path])
        if source_id:
            supabase.mark_profile_source_document_deleted(
                source_id=source_id,
                profile_id=profile_id,
                user_id=user_id,
                deleted_at=datetime.now(tz=UTC).isoformat(),
            )
        raw_document_retained = False
    analysis = analyze_linkedin_profile(parsed)
    evidence = linkedin_evidence(profile_id=profile_id, source_id=source_id, analysis=analysis)
    created_evidence = create_evidence(supabase, evidence)
    updated_profile = update_optional_source(
        supabase=supabase,
        profile=profile,
        profile_id=profile_id,
        user_id=user_id,
        source_key="linkedin",
        value=analysis.model_dump(),
    )
    return LinkedInSourceResponse(
        source_id=source_id,
        profile_id=profile_id,
        source_type=parsed.source_type,
        status="analyzed",
        headline=analysis.headline,
        skill_signals=analysis.skill_signals,
        experience_count=len(analysis.experience_items),
        evidence_count=len(created_evidence),
        profile_version=updated_profile.get("version"),
        delete_after_parsing=delete_after_parsing,
        raw_document_retained=raw_document_retained,
    )
