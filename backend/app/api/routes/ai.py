from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai.application_materials import (
    application_materials_context_hash,
    build_application_materials_context,
)
from app.ai.career_transition import (
    CareerTransitionResult,
    build_career_transition_context,
    career_transition_context_hash,
    generate_career_transition_analysis,
)
from app.ai.claim_verification import (
    ClaimVerificationResult,
    build_claim_verification_context,
    claim_verification_context_hash,
    generate_claim_verification_questions,
)
from app.ai.context import ai_context_hash, build_ai_interpretation_context
from app.ai.interview import build_interview_prep_context, interview_context_hash
from app.ai.llm import AIClient
from app.ai.markdown import (
    application_materials_markdown,
    career_transition_markdown,
    claim_verification_markdown,
    interpretation_markdown,
    interview_markdown,
    learning_plan_markdown,
    outreach_markdown,
    project_roadmap_markdown,
    rewrite_markdown,
    tailoring_markdown,
)
from app.ai.outreach import (
    OutreachMessagePack,
    build_outreach_context,
    generate_outreach_message_pack,
    outreach_context_hash,
)
from app.ai.providers import AIProviderError
from app.ai.resume_rewrite import build_resume_rewrite_context, rewrite_context_hash
from app.ai.roadmap import (
    build_learning_plan_context,
    build_project_roadmap_context,
    learning_plan_context_hash,
    project_roadmap_context_hash,
)
from app.ai.schemas import (
    AIInterpretationResult,
    ApplicationMaterialsResult,
    InterviewPrepResult,
    LearningPlanResult,
    ProjectRoadmapResult,
    ResumeRewriteResult,
    ResumeTailoringPackageResult,
)
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
LEARNING_PLAN_OUTPUT_TYPE = "ai_learning_plan"
LEARNING_PLAN_PROMPT_VERSION = "ai-learning-plan-v1"
APPLICATION_MATERIALS_OUTPUT_TYPE = "ai_application_materials"
APPLICATION_MATERIALS_PROMPT_VERSION = "ai-application-materials-v1"
CLAIM_VERIFICATION_OUTPUT_TYPE = "ai_claim_verification_questions"
CLAIM_VERIFICATION_PROMPT_VERSION = "ai-claim-verification-v1"
OUTREACH_OUTPUT_TYPE = "ai_outreach_message_pack"
OUTREACH_PROMPT_VERSION = "deterministic-outreach-v1"
CAREER_TRANSITION_OUTPUT_TYPE = "ai_career_transition_analysis"
CAREER_TRANSITION_PROMPT_VERSION = "deterministic-career-transition-v1"


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
                "result_markdown": interpretation_markdown(result),
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
                "result_markdown": rewrite_markdown(result),
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
                "result_markdown": tailoring_markdown(result),
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
                "result_markdown": interview_markdown(result),
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
    "/claim-verification-questions",
    response_model=ClaimVerificationResult,
    status_code=status.HTTP_201_CREATED,
)
def create_claim_verification_questions(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> ClaimVerificationResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating claim questions.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        context = build_claim_verification_context(
            normalized_profile=normalized_profile,
            structured_job=structured_job,
        )
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = claim_verification_context_hash(context)
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=CLAIM_VERIFICATION_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = ClaimVerificationResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = generate_claim_verification_questions(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": CLAIM_VERIFICATION_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": CLAIM_VERIFICATION_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": claim_verification_markdown(result),
                "status": "completed",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return result


@router.post(
    "/outreach-message-pack",
    response_model=OutreachMessagePack,
    status_code=status.HTTP_201_CREATED,
)
def create_outreach_message_pack(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> OutreachMessagePack:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating outreach messages.",
            )
        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_outreach_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        input_hash = outreach_context_hash(context)
        cached = supabase.get_generated_output(
            user_id=user.id,
            profile_id=profile_id,
            output_type=OUTREACH_OUTPUT_TYPE,
            input_hash=input_hash,
            job_description_id=job_description_id,
        )
        if cached is not None:
            result = OutreachMessagePack(**(cached.get("result_json") or {}))
            result.cached = True
            return result
        result = generate_outreach_message_pack(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": OUTREACH_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": OUTREACH_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": outreach_markdown(result),
                "status": "completed",
            }
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
    return result


@router.post(
    "/career-transition-analysis",
    response_model=CareerTransitionResult,
    status_code=status.HTTP_201_CREATED,
)
def create_career_transition_analysis(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> CareerTransitionResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating transition analysis.",
            )
        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_career_transition_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        input_hash = career_transition_context_hash(context)
        cached = supabase.get_generated_output(
            user_id=user.id,
            profile_id=profile_id,
            output_type=CAREER_TRANSITION_OUTPUT_TYPE,
            input_hash=input_hash,
            job_description_id=job_description_id,
        )
        if cached is not None:
            result = CareerTransitionResult(**(cached.get("result_json") or {}))
            result.cached = True
            return result
        result = generate_career_transition_analysis(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": CAREER_TRANSITION_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": CAREER_TRANSITION_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": career_transition_markdown(result),
                "status": "completed",
            }
        )
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
                "result_markdown": project_roadmap_markdown(result),
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
    "/learning-plan",
    response_model=LearningPlanResult,
    status_code=status.HTTP_201_CREATED,
)
def create_learning_plan(
    profile_id: str,
    payload: AIInterpretationRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> LearningPlanResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before generating a learning plan.",
            )

        job_description_id = payload.job_description_id if payload else None
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=job_description_id,
        )
        readiness = build_readiness_dashboard(normalized_profile, structured_job)
        context = build_learning_plan_context(
            normalized_profile=normalized_profile,
            readiness=readiness,
            structured_job=structured_job,
        )
        force_regenerate = bool(payload.force_regenerate) if payload else False
        if force_regenerate:
            context["generation_mode"] = "alternate"
        input_hash = learning_plan_context_hash(context)
        if not force_regenerate:
            cached = supabase.get_generated_output(
                user_id=user.id,
                profile_id=profile_id,
                output_type=LEARNING_PLAN_OUTPUT_TYPE,
                input_hash=input_hash,
                job_description_id=job_description_id,
            )
            if cached is not None:
                result = LearningPlanResult(**(cached.get("result_json") or {}))
                result.cached = True
                return result

        result = AIClient(supabase.settings).generate_learning_plan(context)
        supabase.create_generated_output(
            {
                "user_id": user.id,
                "profile_id": profile_id,
                "output_type": LEARNING_PLAN_OUTPUT_TYPE,
                "job_description_id": job_description_id,
                "input_hash": input_hash,
                "prompt_version": LEARNING_PLAN_PROMPT_VERSION,
                "provider": result.provider,
                "model_name": result.model_name,
                "result_json": result.model_dump(exclude={"cached"}),
                "result_markdown": learning_plan_markdown(result),
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
                "result_markdown": application_materials_markdown(result),
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
