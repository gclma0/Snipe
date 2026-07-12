from datetime import UTC, datetime
from hashlib import sha256

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.analysis.github_profile import analyze_github_profile, github_evidence
from app.api.routes.source_common import CurrentUser, Supabase
from app.auth.dependencies import AuthenticatedUser
from app.core.config import get_settings
from app.integrations.github import GitHubClient, GitHubLookupError
from app.supabase.client import SupabaseClient, SupabaseError

router = APIRouter()


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
