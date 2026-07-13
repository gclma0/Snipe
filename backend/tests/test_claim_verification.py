from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.ai.claim_verification import (
    build_claim_verification_context,
    generate_claim_verification_questions,
)
from app.ai.llm import _local_template_interview_prep
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.scoring.readiness import build_readiness_dashboard
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_JOB_ID = "22222222-2222-2222-2222-222222222222"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    settings: Settings
    profile: dict[str, Any] | None
    job_description: dict[str, Any] | None = None
    cached_output: dict[str, Any] | None = None
    generated_outputs: list[dict[str, Any]] = field(default_factory=list)

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

    def get_generated_output(self, **_: Any) -> dict[str, Any] | None:
        return self.cached_output

    def create_generated_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.generated_outputs.append(payload)
        return {**payload, "id": "generated-1"}


def client_with_fake_supabase(fake: FakeSupabaseClient) -> TestClient:
    app = create_app(fake.settings)
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
            "projects": "Created a portfolio dashboard project using Python and SQL.",
        },
    }


def structured_job() -> dict[str, Any]:
    return {
        "title": "Data Analyst",
        "required_skills": ["python", "sql", "excel"],
        "preferred_skills": ["communication"],
        "tools": [],
        "soft_skills": ["communication"],
    }


def test_claim_questions_use_evidence_strength_language_without_banned_wording() -> None:
    context = build_claim_verification_context(
        normalized_profile=normalized_profile(),
        structured_job=structured_job(),
    )

    result = generate_claim_verification_questions(context)
    serialized = result.model_dump_json().lower()

    assert result.questions
    assert {question.evidence_strength for question in result.questions} >= {
        "strong",
        "moderate",
        "missing",
    }
    assert "evidence strength" in " ".join(result.evidence_strength_notes).lower()
    assert "lie detector" not in serialized
    assert "detect lies" not in serialized


def test_interview_prep_includes_milestone_question_categories() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = {
        "verified_skills": ["python", "sql", "communication"],
        "experience_signals": [
            "Built SQL dashboards and explained weekly trends to operations leaders.",
            "Created a portfolio dashboard project using Python and SQL.",
        ],
        "target_job": structured_job(),
        "skill_gap": {
            "matched": ["python", "sql", "communication"],
            "missing": ["excel"],
        },
        "readiness": {
            "overall": readiness.scores.overall,
            "primary_specialization": "data analytics",
        },
    }

    result = _local_template_interview_prep(context)
    categories = {question.category for question in result.questions}

    assert {
        "role_specific",
        "technical",
        "behavioral",
        "situational",
        "resume_based",
        "project_based",
        "leadership",
        "career_transition",
        "job_specific",
        "screening",
    }.issubset(categories)


def test_claim_verification_endpoint_generates_and_persists_output() -> None:
    settings = Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    fake = FakeSupabaseClient(
        settings=settings,
        profile={"id": TEST_PROFILE_ID, "version": 1, "normalized_json": normalized_profile()},
        job_description={"id": TEST_JOB_ID, "structured_json": structured_job()},
    )
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/claim-verification-questions",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["output_type"] == "ai_claim_verification_questions"
    assert body["questions"]
    assert fake.generated_outputs[0]["output_type"] == "ai_claim_verification_questions"
    assert "Evidence strength" in fake.generated_outputs[0]["result_markdown"]


def test_claim_verification_endpoint_returns_cached_output() -> None:
    settings = Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    cached = generate_claim_verification_questions(
        build_claim_verification_context(
            normalized_profile=normalized_profile(),
            structured_job=structured_job(),
        )
    ).model_dump(exclude={"cached"})
    fake = FakeSupabaseClient(
        settings=settings,
        profile={"id": TEST_PROFILE_ID, "version": 1, "normalized_json": normalized_profile()},
        job_description={"id": TEST_JOB_ID, "structured_json": structured_job()},
        cached_output={"result_json": cached},
    )
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/claim-verification-questions",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert fake.generated_outputs == []
