from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.jobs.job_parser import parse_job_description
from app.jobs.schemas import StructuredJobDescription
from app.parsing.resume_parser import SUPPORTED_RESUME_EXTENSIONS, parse_resume, resume_extension
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/job-descriptions", tags=["job descriptions"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)

MAX_JOB_DESCRIPTION_BYTES = 4 * 1024 * 1024


class JobDescriptionCreate(BaseModel):
    text: str = Field(min_length=100, max_length=60000)


class JobDescriptionResponse(BaseModel):
    id: str | None = None
    profile_id: str
    source_type: str
    input_hash: str
    structured: StructuredJobDescription


@router.post("", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_job_description_from_text(
    profile_id: str,
    payload: JobDescriptionCreate,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> JobDescriptionResponse:
    return _create_job_description(
        profile_id=profile_id,
        user=user,
        supabase=supabase,
        text=payload.text,
        source_type="pasted_text",
    )


@router.post("/upload", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description_from_upload(
    profile_id: str,
    file: Annotated[UploadFile, File(...)],
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> JobDescriptionResponse:
    filename = file.filename or ""
    extension = resume_extension(filename)
    if extension not in SUPPORTED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Job description upload must be a PDF or DOCX file.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description file is empty.",
        )
    if len(content) > MAX_JOB_DESCRIPTION_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Job description file must be 4 MB or smaller.",
        )

    parsed = parse_resume(filename, content)
    if parsed.text_length < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text is too short to analyze.",
        )

    return _create_job_description(
        profile_id=profile_id,
        user=user,
        supabase=supabase,
        text=parsed.text,
        source_type=f"uploaded_{extension.lstrip('.')}",
    )


def _create_job_description(
    *,
    profile_id: str,
    user: AuthenticatedUser,
    supabase: SupabaseClient,
    text: str,
    source_type: str,
) -> JobDescriptionResponse:
    try:
        if not supabase.profile_belongs_to_user(profile_id=profile_id, user_id=user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        structured = parse_job_description(text)
        input_hash = sha256(text.encode("utf-8")).hexdigest()
        row = supabase.create_job_description(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "title": structured.title,
                "company": structured.company,
                "source_type": source_type,
                "input_hash": input_hash,
                "raw_text": text,
                "structured_json": structured.model_dump(),
                "parser_version": structured.parser_version,
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return JobDescriptionResponse(
        id=row.get("id"),
        profile_id=profile_id,
        source_type=source_type,
        input_hash=input_hash,
        structured=structured,
    )
