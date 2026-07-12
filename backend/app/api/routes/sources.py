from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.parsing.resume_parser import SUPPORTED_RESUME_EXTENSIONS, parse_resume, resume_extension
from app.storage.paths import candidate_document_path
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/sources", tags=["sources"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)

MAX_RESUME_BYTES = 8 * 1024 * 1024


class ResumeUploadResponse(BaseModel):
    source_id: str | None = None
    profile_id: str
    source_type: str
    original_filename: str
    storage_path: str
    content_hash: str
    parsed_text_hash: str
    parser_version: str
    status: str
    text_length: int = Field(ge=0)
    page_count: int | None = Field(default=None, ge=0)
    paragraph_count: int | None = Field(default=None, ge=0)


@router.post("/resume", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume_source(
    profile_id: str,
    file: Annotated[UploadFile, File(...)],
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ResumeUploadResponse:
    filename = file.filename or ""
    extension = resume_extension(filename)
    if extension not in SUPPORTED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Resume must be a PDF or DOCX file.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file is empty.")
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Resume file must be 8 MB or smaller.",
        )

    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        parsed = parse_resume(filename, content)
        content_hash = sha256(content).hexdigest()
        parsed_text_hash = sha256(parsed.text.encode("utf-8")).hexdigest()
        storage_path = candidate_document_path(user.id, profile_id, filename)
        supabase.upload_document(
            path=storage_path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        source = supabase.create_profile_source(
            {
                "profile_id": profile_id,
                "user_id": user.id,
                "source_type": parsed.source_type,
                "storage_path": storage_path,
                "original_filename": filename,
                "content_hash": content_hash,
                "parsed_text_hash": parsed_text_hash,
                "parser_version": parsed.parser,
                "status": "parsed",
                "parsed_at": datetime.now(tz=UTC).isoformat(),
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return ResumeUploadResponse(
        source_id=source.get("id"),
        profile_id=profile_id,
        source_type=parsed.source_type,
        original_filename=filename,
        storage_path=storage_path,
        content_hash=content_hash,
        parsed_text_hash=parsed_text_hash,
        parser_version=parsed.parser,
        status="parsed",
        text_length=parsed.text_length,
        page_count=parsed.page_count,
        paragraph_count=parsed.paragraph_count,
    )
