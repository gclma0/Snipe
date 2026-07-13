from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai.application_materials import (
    application_materials_context_hash,
    build_application_materials_context,
)
from app.ai.context import ai_context_hash, build_ai_interpretation_context
from app.ai.interview import build_interview_prep_context, interview_context_hash
from app.ai.llm import (
    AIClient,
    AIInterpretationResult,
    AIProviderError,
    ApplicationMaterialsResult,
    InterviewPrepResult,
    ProjectRoadmapResult,
    ResumeRewriteResult,
    ResumeTailoringPackageResult,
)
from app.ai.resume_rewrite import build_resume_rewrite_context, rewrite_context_hash
from app.ai.roadmap import build_project_roadmap_context, project_roadmap_context_hash
from app.ai.tailoring import build_resume_tailoring_context, tailoring_context_hash
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
TAILORING_OUTPUT_TYPE = "ai_resume_tailoring_package"
TAILORING_PROMPT_VERSION = "ai-resume-tailoring-package-v1"
INTERVIEW_OUTPUT_TYPE = "ai_interview_prep"
INTERVIEW_PROMPT_VERSION = "ai-interview-prep-v1"
PROJECT_ROADMAP_OUTPUT_TYPE = "ai_project_roadmap_recommendations"
PROJECT_ROADMAP_PROMPT_VERSION = "ai-project-roadmap-v1"
APPLICATION_MATERIALS_OUTPUT_TYPE = "ai_application_materials"
APPLICATION_MATERIALS_PROMPT_VERSION = "ai-application-materials-v1"


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
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = ai_context_hash(context)
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
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = rewrite_context_hash(context)
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


@router.post(
    "/resume-tailoring-package",
    response_model=ResumeTailoringPackageResult,
    status_code=status.HTTP_201_CREATED,
)
def create_resume_tailoring_package(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ResumeTailoringPackageResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating a tailoring package.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_resume_tailoring_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = tailoring_context_hash(context)
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=TAILORING_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = ResumeTailoringPackageResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_resume_tailoring_package(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": TAILORING_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": TAILORING_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": _tailoring_markdown(result),
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
    "/interview-prep",
    response_model=InterviewPrepResult,
    status_code=status.HTTP_201_CREATED,
)
def create_interview_prep(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> InterviewPrepResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating interview prep.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_interview_prep_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = interview_context_hash(context)
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=INTERVIEW_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = InterviewPrepResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_interview_prep(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": INTERVIEW_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": INTERVIEW_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": _interview_markdown(result),
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
    "/project-roadmap-recommendations",
    response_model=ProjectRoadmapResult,
    status_code=status.HTTP_201_CREATED,
)
def create_project_roadmap_recommendations(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ProjectRoadmapResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating project recommendations.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_project_roadmap_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = project_roadmap_context_hash(context)
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=PROJECT_ROADMAP_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = ProjectRoadmapResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_project_roadmap(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": PROJECT_ROADMAP_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": PROJECT_ROADMAP_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": _project_roadmap_markdown(result),
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
    "/application-materials",
    response_model=ApplicationMaterialsResult,
    status_code=status.HTTP_201_CREATED,
)
def create_application_materials(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ApplicationMaterialsResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating application materials.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_application_materials_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = application_materials_context_hash(context)
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=APPLICATION_MATERIALS_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = ApplicationMaterialsResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_application_materials(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": APPLICATION_MATERIALS_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": APPLICATION_MATERIALS_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": _application_materials_markdown(result),
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


def _tailoring_markdown(result: ResumeTailoringPackageResult) -> str:
    lines = ["# Snipe Resume Tailoring Package", "", result.summary, ""]
    lines.extend(["## Tailored Summary", result.tailored_summary, ""])
    if result.skill_order:
        lines.append("## Skill Order")
        lines.extend(f"- {skill}" for skill in result.skill_order)
        lines.append("")
    if result.keyword_recommendations:
        lines.append("## Keyword Recommendations")
        for item in result.keyword_recommendations:
            lines.extend(
                [
                    f"- {item.keyword}: {item.placement}",
                    f"  Reason: {item.reason}",
                ]
            )
        lines.append("")
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def _interview_markdown(result: InterviewPrepResult) -> str:
    lines = ["# Snipe Interview Prep", "", result.summary, ""]
    if result.star_guidance:
        lines.append("## STAR Guidance")
        lines.extend(f"- {item}" for item in result.star_guidance)
        lines.append("")
    if result.questions:
        lines.append("## Practice Questions")
        for item in result.questions:
            lines.extend(
                [
                    f"### {item.category.replace('_', ' ').title()}",
                    item.question,
                    f"Why: {item.why_it_matters}",
                    f"Guidance: {item.answer_guidance}",
                    "",
                ]
            )
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def _project_roadmap_markdown(result: ProjectRoadmapResult) -> str:
    lines = ["# Snipe Project Roadmap", "", result.summary, ""]
    if result.projects:
        lines.append("## Project Recommendations")
        for item in result.projects:
            lines.extend(
                [
                    f"### {item.title}",
                    item.objective,
                    "",
                    "Skills practiced:",
                    *[f"- {skill}" for skill in item.skills_practiced],
                    "Deliverables:",
                    *[f"- {deliverable}" for deliverable in item.deliverables],
                    "",
                ]
            )
    if result.roadmap:
        lines.append("## Roadmap")
        for item in result.roadmap:
            lines.extend(
                [
                    f"### {item.timeframe.replace('_', ' ').title()}",
                    item.focus,
                    "",
                    "Actions:",
                    *[f"- {action}" for action in item.actions],
                    "Success criteria:",
                    *[f"- {criterion}" for criterion in item.success_criteria],
                    "",
                ]
            )
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def _application_materials_markdown(result: ApplicationMaterialsResult) -> str:
    lines = ["# Snipe Application Materials", "", result.summary, ""]
    lines.extend(["## Cover Letter", result.cover_letter, ""])
    lines.extend(["## Concise Cover Note", result.concise_cover_note, ""])
    lines.extend(["## Email Application", result.email_application, ""])
    if result.evidence_used:
        lines.append("## Evidence Used")
        lines.extend(f"- {item}" for item in result.evidence_used)
        lines.append("")
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)
