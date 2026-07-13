import re
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, Field

from app.ai.answer_evaluation import AnswerEvaluationResult, evaluate_answer

MOCK_INTERVIEW_VERSION = "deterministic-mock-interview-v1"


class MockInterviewQuestion(BaseModel):
    category: str
    question: str
    evidence_to_use: list[str] = Field(default_factory=list, max_length=5)


class MockInterviewTranscriptItem(BaseModel):
    question: MockInterviewQuestion
    answer: str
    evaluation: AnswerEvaluationResult
    follow_up_question: str


class MockInterviewSession(BaseModel):
    session_id: str
    version: str = MOCK_INTERVIEW_VERSION
    status: Literal["active", "completed"] = "active"
    current_index: int = Field(ge=0)
    questions: list[MockInterviewQuestion] = Field(default_factory=list, max_length=8)
    transcript: list[MockInterviewTranscriptItem] = Field(default_factory=list, max_length=8)


class MockInterviewTurnResult(BaseModel):
    session: MockInterviewSession
    evaluation: AnswerEvaluationResult
    follow_up_question: str
    next_question: MockInterviewQuestion | None = None


def start_mock_interview_session(
    *,
    normalized_profile: dict,
    structured_job: dict | None,
    question_count: int = 5,
) -> MockInterviewSession:
    skills = _skills(normalized_profile)
    experience = _experience_signals(normalized_profile)
    role = _role_name(structured_job)
    required = _job_list(structured_job, "required_skills")
    questions = [
        MockInterviewQuestion(
            category="role_specific",
            question=f"How would you approach the main responsibilities of {role}?",
            evidence_to_use=(skills[:2] or experience[:1]),
        ),
        MockInterviewQuestion(
            category="resume_based",
            question="Walk me through the strongest experience on your profile.",
            evidence_to_use=experience[:2],
        ),
        MockInterviewQuestion(
            category="behavioral",
            question="Tell me about a time you handled a challenge with other people involved.",
            evidence_to_use=experience[:2],
        ),
        MockInterviewQuestion(
            category="technical" if required else "job_specific",
            question=_skill_question(required[0] if required else (skills[0] if skills else role)),
            evidence_to_use=required[:1] if required else skills[:1],
        ),
        MockInterviewQuestion(
            category="situational",
            question=f"What would you prioritize in your first 30 days in {role}?",
            evidence_to_use=(required[:2] or skills[:2]),
        ),
    ][: max(1, min(question_count, 5))]
    seed = "|".join(question.question for question in questions)
    return MockInterviewSession(
        session_id=sha256(seed.encode("utf-8")).hexdigest()[:16],
        current_index=0,
        questions=questions,
    )


def answer_mock_interview_question(
    *,
    session: MockInterviewSession,
    answer: str,
) -> MockInterviewTurnResult:
    if session.status == "completed" or session.current_index >= len(session.questions):
        raise ValueError("Mock interview session is already completed.")
    question = session.questions[session.current_index]
    evaluation = evaluate_answer(
        question=question.question,
        answer=answer,
        evidence_to_use=question.evidence_to_use,
        category=question.category,
    )
    transcript_item = MockInterviewTranscriptItem(
        question=question,
        answer=answer,
        evaluation=evaluation,
        follow_up_question=evaluation.follow_up_question,
    )
    next_index = session.current_index + 1
    updated = session.model_copy(
        update={
            "current_index": next_index,
            "status": "completed" if next_index >= len(session.questions) else "active",
            "transcript": [*session.transcript, transcript_item],
        }
    )
    next_question = None if updated.status == "completed" else updated.questions[next_index]
    return MockInterviewTurnResult(
        session=updated,
        evaluation=evaluation,
        follow_up_question=evaluation.follow_up_question,
        next_question=next_question,
    )


def _skills(normalized_profile: dict) -> list[str]:
    values = normalized_profile.get("skills")
    if not isinstance(values, list):
        return []
    names = []
    for item in values:
        value = item.get("name") if isinstance(item, dict) else item
        if isinstance(value, str) and value.strip():
            names.append(value.strip().lower())
    return sorted(set(names))[:10]


def _experience_signals(normalized_profile: dict) -> list[str]:
    sections = normalized_profile.get("sections")
    if not isinstance(sections, dict):
        return []
    text = sections.get("experience") or sections.get("projects") or sections.get("summary")
    if not isinstance(text, str):
        return []
    signals = []
    for part in re.split(r"[\n.;]+", text):
        cleaned = " ".join(part.strip().split())
        if len(cleaned) >= 12:
            signals.append(cleaned[:180])
    return signals[:4]


def _job_list(structured_job: dict | None, key: str) -> list[str]:
    if not structured_job:
        return []
    value = structured_job.get(key)
    if not isinstance(value, list):
        return []
    return [item.lower() for item in value if isinstance(item, str)][:8]


def _role_name(structured_job: dict | None) -> str:
    if structured_job and isinstance(structured_job.get("title"), str):
        return structured_job["title"]
    return "the target role"


def _skill_question(skill: str) -> str:
    return f"Tell me about a real example where you used {skill}."
