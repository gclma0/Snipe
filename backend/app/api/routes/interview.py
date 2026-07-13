from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.ai.answer_evaluation import AnswerEvaluationResult, evaluate_answer
from app.ai.mock_interview import (
    MockInterviewSession,
    MockInterviewTurnResult,
    answer_mock_interview_question,
    start_mock_interview_session,
)
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/profiles/{profile_id}/interview", tags=["interview"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


class StartMockInterviewRequest(BaseModel):
    job_description_id: str | None = None
    question_count: int = Field(default=5, ge=1, le=5)


class MockInterviewAnswerRequest(BaseModel):
    session: MockInterviewSession
    answer: str = Field(min_length=1, max_length=8000)


class StandaloneAnswerEvaluationRequest(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    answer: str = Field(min_length=1, max_length=8000)
    evidence_to_use: list[str] = Field(default_factory=list, max_length=8)
    category: str | None = Field(default=None, max_length=80)


@router.post("/sessions", response_model=MockInterviewSession, status_code=status.HTTP_201_CREATED)
def create_mock_interview_session(
    profile_id: str,
    payload: StartMockInterviewRequest | None = None,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> MockInterviewSession:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        normalized_profile = profile.get("normalized_json") or {}
        if not normalized_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload and parse a resume before starting a mock interview.",
            )
        structured_job = _get_structured_job(
            supabase=supabase,
            user_id=user.id,
            profile_id=profile_id,
            job_description_id=payload.job_description_id if payload else None,
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return start_mock_interview_session(
        normalized_profile=normalized_profile,
        structured_job=structured_job,
        question_count=payload.question_count if payload else 5,
    )


@router.post(
    "/sessions/messages",
    response_model=MockInterviewTurnResult,
    status_code=status.HTTP_201_CREATED,
)
def answer_mock_interview(
    profile_id: str,
    payload: MockInterviewAnswerRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> MockInterviewTurnResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
        return answer_mock_interview_question(session=payload.session, answer=payload.answer)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.post(
    "/answer-evaluation",
    response_model=AnswerEvaluationResult,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_standalone_answer(
    profile_id: str,
    payload: StandaloneAnswerEvaluationRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> AnswerEvaluationResult:
    try:
        profile = supabase.get_candidate_profile(profile_id=profile_id, user_id=user.id)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc

    return evaluate_answer(
        question=payload.question,
        answer=payload.answer,
        evidence_to_use=payload.evidence_to_use,
        category=payload.category,
    )


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
