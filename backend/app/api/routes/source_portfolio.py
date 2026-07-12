from datetime import UTC, datetime
from hashlib import sha256

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.analysis.portfolio import analyze_portfolio_page, portfolio_evidence
from app.api.routes.source_common import (
    CurrentUser,
    Supabase,
    create_evidence,
    update_optional_source,
)
from app.auth.dependencies import AuthenticatedUser
from app.integrations.portfolio import PortfolioClient, PortfolioFetchError
from app.supabase.client import SupabaseClient, SupabaseError

router = APIRouter()


class PortfolioSourceRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)


class PortfolioSourceResponse(BaseModel):
    source_id: str | None = None
    profile_id: str
    url: str
    status: str
    title: str | None = None
    technical_signals: list[str]
    non_technical_signals: list[str]
    project_signal_count: int = Field(ge=0)
    contact_signal_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    profile_version: int | None = Field(default=None, ge=1)


@router.post(
    "/portfolio",
    response_model=PortfolioSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_portfolio_source(
    profile_id: str,
    payload: PortfolioSourceRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> PortfolioSourceResponse:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        page = PortfolioClient().fetch_url(payload.url)
        analysis = analyze_portfolio_page(page)
        source = supabase.create_profile_source(
            {
                "profile_id": profile_id,
                "user_id": user.id,
                "source_type": "portfolio_url",
                "original_filename": page.final_url,
                "content_hash": sha256(page.text.encode("utf-8")).hexdigest(),
                "parsed_text_hash": sha256(page.text.encode("utf-8")).hexdigest(),
                "parser_version": analysis.analysis_version,
                "status": "analyzed",
                "parsed_at": datetime.now(tz=UTC).isoformat(),
            }
        )
        source_id = source.get("id")
        evidence = portfolio_evidence(profile_id=profile_id, source_id=source_id, analysis=analysis)
        created_evidence = create_evidence(supabase, evidence)
        updated_profile = update_optional_source(
            supabase=supabase,
            profile=profile,
            profile_id=profile_id,
            user_id=user.id,
            source_key="portfolio",
            value=analysis.model_dump(),
        )
    except PortfolioFetchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return PortfolioSourceResponse(
        source_id=source_id,
        profile_id=profile_id,
        url=analysis.url,
        status="analyzed",
        title=analysis.title,
        technical_signals=analysis.technical_signals,
        non_technical_signals=analysis.non_technical_signals,
        project_signal_count=analysis.project_signal_count,
        contact_signal_count=analysis.contact_signal_count,
        evidence_count=len(created_evidence),
        profile_version=updated_profile.get("version"),
    )
