from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient

from app.ai.answer_evaluation import evaluate_answer
from app.ai.mock_interview import answer_mock_interview_question, start_mock_interview_session
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_JOB_ID = "22222222-2222-2222-2222-222222222222"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None
    job_description: dict[str, Any] | None = None

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def get_job_description(
        self,
        *,
        job_description_id: str,
        profile_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        if (
            job_description_id != TEST_JOB_ID
            or profile_id != TEST_PROFILE_ID
            or user_id != TEST_USER_ID
        ):
            return None
        return self.job_description


def client_with_fake_supabase(fake: FakeSupabaseClient) -> TestClient:
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET))
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="user@example.com",
        role="authenticated",
        claims={},
    )
    app.dependency_overrides[get_supabase_client] = lambda: fake
    return TestClient(app)


def normalized_profile() -> dict[str, Any]:
    return {
        "skills": [
            {"name": "python", "source": "resume"},
            {"name": "sql", "source": "resume"},
            {"name": "communication", "source": "resume"},
        ],
        "sections": {
            "summary": "Data analyst with Python, SQL, and stakeholder communication.",
            "experience": "Built SQL dashboards and explained weekly trends to operations leaders.",
        },
    }


def structured_job() -> dict[str, Any]:
    return {
        "title": "Data Analyst",
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Excel"],
    }


def test_mock_interview_session_advances_state_and_completes() -> None:
    session = start_mock_interview_session(
        normalized_profile=normalized_profile(),
        structured_job=structured_job(),
        question_count=2,
    )

    first = answer_mock_interview_question(
        session=session,
        answer=(
            "In my profile, I built SQL dashboards. I used Python and SQL to analyze trends, "
            "then explained the outcome to operations leaders."
        ),
    )
    second = answer_mock_interview_question(
        session=first.session,
        answer=(
            "During that work, my task was to make weekly reporting clearer. I created the "
            "dashboard and shared the result with stakeholders."
        ),
    )

    assert first.session.current_index == 1
    assert first.session.status == "active"
    assert first.next_question is not None
    assert second.session.current_index == 2
    assert second.session.status == "completed"
    assert second.next_question is None
    assert len(second.session.transcript) == 2


def test_answer_evaluation_schema_and_follow_up_generation() -> None:
    result = evaluate_answer(
        question="Tell me about a real example where you used SQL.",
        answer="I used SQL.",
        evidence_to_use=["Built SQL dashboards for operations leaders."],
        category="technical",
    )

    assert result.overall_score <= 70
    assert result.follow_up_question
    assert result.star_feedback
    assert result.improvements


def test_improved_answer_does_not_invent_experience_or_metrics() -> None:
    result = evaluate_answer(
        question="Tell me about a real example where you used Python.",
        answer="I used Python in a dashboard project.",
        evidence_to_use=["Created a portfolio dashboard project using Python."],
        category="technical",
    )
    serialized = result.model_dump_json().lower()

    assert "million" not in serialized
    assert "increased revenue" not in serialized
    assert "only include metrics" in serialized


def test_mock_interview_api_start_answer_and_standalone_evaluation() -> None:
    fake = FakeSupabaseClient(
        profile={"id": TEST_PROFILE_ID, "normalized_json": normalized_profile()},
        job_description={"id": TEST_JOB_ID, "structured_json": structured_job()},
    )
    client = client_with_fake_supabase(fake)

    start_response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/interview/sessions",
        json={"job_description_id": TEST_JOB_ID, "question_count": 2},
    )
    assert start_response.status_code == 201
    session = start_response.json()
    assert session["questions"][0]["question"]

    turn_response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/interview/sessions/messages",
        json={
            "session": session,
            "answer": "I built SQL dashboards and explained the outcome to operations leaders.",
        },
    )
    assert turn_response.status_code == 201
    assert turn_response.json()["evaluation"]["overall_score"] >= 0
    assert turn_response.json()["follow_up_question"]

    eval_response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/interview/answer-evaluation",
        json={
            "question": "Tell me about SQL.",
            "answer": "I built SQL dashboards.",
            "evidence_to_use": ["Built SQL dashboards for operations leaders."],
            "category": "technical",
        },
    )
    assert eval_response.status_code == 201
    assert eval_response.json()["output_type"] == "interview_answer_evaluation"
