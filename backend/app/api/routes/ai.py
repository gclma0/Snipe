from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai.context import ai_context_hash, build_ai_interpretation_context
from app.ai.llm import AIClient, AIInterpretationResult, AIProviderError, ResumeRewriteResult
from app.ai.resume_rewrite import build_resume_rewrite_context, rewrite_context_hash
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.scoring.readiness import build_readiness_dashboard
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/ai", tags=["ai"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)

OUTPUT_TYPE = "ai_readiness_interpretation"
PROMPT_VERSION = "ai-readiness-interpretation-v1"
REWRITE_OUTPUT_TYPE = "ai_resume_rewrite_suggestions"
REWRITE_PROMPT_VERSION = "ai-resume-rewrite-suggestions-v1"


class AIInterpretationRequest(BaseModel):
    job_description_id: str | None = None
    force_regenerate: bool = False


@router.post(
    "/readiness-interpretation",
    response_model=AIInterpretationResult,
    status_code=status.HTTP_201_CREATED,
)
def create_ai_readiness_interpretation(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> AIInterpretationResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating an AI interpretation.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_ai_interpretation_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        input_hash = ai_context_hash(context)
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = AIInterpretationResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_interpretation(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": _markdown(result),
                "status": "completed",
            }
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result


@router.post(
    "/resume-rewrite-suggestions",
    response_model=ResumeRewriteResult,
    status_code=status.HTTP_201_CREATED,
)
def create_resume_rewrite_suggestions(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ResumeRewriteResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating rewrite suggestions.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_resume_rewrite_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        input_hash = rewrite_context_hash(context)
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=REWRITE_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = ResumeRewriteResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_resume_rewrite_suggestions(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": REWRITE_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": REWRITE_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": _rewrite_markdown(result),
                "status": "completed",
            }
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result


def _get_structured_job(
    *,
    supabase: SupabaseClient,
    user_id: str,
    profile_id: str,
    job_description_id: str | None,
) -> dict | None:
    if not job_description_id:
        return None
    job_description = supabase.get_job_description(
        job_description_id=job_description_id,
        profile_id=profile_id,
        user_id=user_id,
    )
    if job_description is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found.",
        )
    return job_description.get("structured_json") or {}


def _markdown(result: AIInterpretationResult) -> str:
    lines = ["# Snipe AI Interpretation", "", result.summary, "", result.readiness_explanation, ""]
    lines.append("## Recommendations")
    for item in result.recommendations:
        lines.extend(["", f"### {item.title}", item.rationale, item.action])
    if result.cautions:
        lines.extend(["", "## Cautions"])
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def _rewrite_markdown(result: ResumeRewriteResult) -> str:
    lines = ["# Snipe Resume Rewrite Suggestions", "", result.summary, ""]
    for item in result.suggestions:
        lines.extend(
            [
                "## Suggestion",
                f"Original: {item.original}",
                f"Suggested: {item.suggested}",
                f"Why: {item.rationale}",
                "",
            ]
        )
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)
