from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.analysis.github_profile import analyze_github_profile, github_evidence
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import get_settings
from app.integrations.github import GitHubClient, GitHubLookupError
from app.parsing.resume_parser import SUPPORTED_RESUME_EXTENSIONS, parse_resume, resume_extension
from app.profile.profile_builder import build_normalized_profile
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
    profile_version: int | None = Field(default=None, ge=1)
    evidence_count: int = Field(default=0, ge=0)
    normalized_profile_updated: bool = False


class GitHubSourceRequest(BaseModel):
    username_or_url: str = Field(min_length=1, max_length=120)


class GitHubSourceResponse(BaseModel):
    source_id: str | None = None
    profile_id: str
    username: str
    status: str
    repository_count: int = Field(ge=0)
    analyzed_repository_count: int = Field(ge=0)
    primary_languages: list[str]
    readme_repository_count: int = Field(ge=0)
    test_signal_count: int = Field(ge=0)
    ci_signal_count: int = Field(ge=0)
    notable_repositories: list[str]
    evidence_count: int = Field(ge=0)
    profile_version: int | None = Field(default=None, ge=1)


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
        source_id = source.get("id")
        built_profile = build_normalized_profile(
            parsed=parsed,
            profile_id=profile_id,
            source_id=source_id,
        )
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        next_version = int(profile.get("version") or 1) + 1
        updated_profile = supabase.update_candidate_profile(
            profile_id=profile_id,
            user_id=user.id,
            payload={
                "version": next_version,
                "profile_status": "resume_parsed",
                "normalized_json": built_profile.normalized_json,
                "updated_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        evidence_rows = [
            {
                "profile_id": profile_id,
                "source_id": source_id,
                "fact_type": item.fact_type,
                "fact_key": item.fact_key,
                "excerpt": item.excerpt,
                "normalized_value": item.normalized_value,
                "confidence": item.confidence,
                "location_json": item.location_json,
            }
            for item in built_profile.evidence
        ]
        created_evidence = supabase.create_profile_evidence(evidence_rows)
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
        profile_version=updated_profile.get("version"),
        evidence_count=len(created_evidence),
        normalized_profile_updated=True,
    )


@router.post("/github", response_model=GitHubSourceResponse, status_code=status.HTTP_201_CREATED)
def add_github_source(
    profile_id: str,
    payload: GitHubSourceRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> GitHubSourceResponse:
    settings = get_settings()
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        github_profile = GitHubClient(settings.github_token).fetch_public_profile(
            payload.username_or_url
        )
        analysis = analyze_github_profile(github_profile)
        source = supabase.create_profile_source(
            {
                "profile_id": profile_id,
                "user_id": user.id,
                "source_type": "github_public",
                "original_filename": github_profile.html_url,
                "content_hash": sha256(
                    github_profile.model_dump_json().encode("utf-8")
                ).hexdigest(),
                "parser_version": analysis.analysis_version,
                "status": "analyzed",
                "parsed_at": datetime.now(tz=UTC).isoformat(),
            }
        )
        source_id = source.get("id")
        evidence = github_evidence(profile_id=profile_id, source_id=source_id, analysis=analysis)
        created_evidence = supabase.create_profile_evidence(
            [
                {
                    "profile_id": profile_id,
                    "source_id": source_id,
                    "fact_type": item.fact_type,
                    "fact_key": item.fact_key,
                    "excerpt": item.excerpt,
                    "normalized_value": item.normalized_value,
                    "confidence": item.confidence,
                    "location_json": item.location_json,
                }
                for item in evidence
            ]
        )
        normalized_json = profile.get("normalized_json") or {}
        optional_sources = normalized_json.setdefault("optional_sources", {})
        optional_sources["github"] = analysis.model_dump()
        next_version = int(profile.get("version") or 1) + 1
        updated_profile = supabase.update_candidate_profile(
            profile_id=profile_id,
            user_id=user.id,
            payload={
                "version": next_version,
                "normalized_json": normalized_json,
                "updated_at": datetime.now(tz=UTC).isoformat(),
            },
        )
    except GitHubLookupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return GitHubSourceResponse(
        source_id=source_id,
        profile_id=profile_id,
        username=analysis.username,
        status="analyzed",
        repository_count=analysis.repository_count,
        analyzed_repository_count=analysis.analyzed_repository_count,
        primary_languages=analysis.primary_languages,
        readme_repository_count=analysis.readme_repository_count,
        test_signal_count=analysis.test_signal_count,
        ci_signal_count=analysis.ci_signal_count,
        notable_repositories=analysis.notable_repositories,
        evidence_count=len(created_evidence),
        profile_version=updated_profile.get("version"),
    )
