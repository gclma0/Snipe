from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.ai.career_transition import (
    build_career_transition_context,
    generate_career_transition_analysis,
)
from app.ai.outreach import build_outreach_context, generate_outreach_message_pack
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
            {"name": "excel", "source": "resume"},
            {"name": "sql", "source": "resume"},
            {"name": "communication", "source": "resume"},
        ],
        "sections": {
            "summary": "Operations analyst moving toward data analytics.",
            "experience": "Built weekly Excel reports and explained trends to managers.",
        },
    }


def structured_job() -> dict[str, Any]:
    return {
        "title": "Data Analyst",
        "company": "Example Co",
        "required_skills": ["sql", "python", "tableau"],
        "preferred_skills": ["communication"],
        "tools": ["excel"],
        "soft_skills": ["communication"],
    }


def test_outreach_messages_use_placeholders_and_verified_evidence_only() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_outreach_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = generate_outreach_message_pack(context)
    serialized = result.model_dump_json().lower()

    assert "[name]" in result.linkedin_connection_message
    assert "[candidate name]" in result.job_application_email
    assert "excel" in serialized
    assert "sql" in serialized
    assert "increased revenue" not in serialized
    assert "10x" not in serialized


def test_career_transition_analysis_recommends_realistic_next_steps() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_career_transition_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = generate_career_transition_analysis(context)

    assert "sql" in result.transferable_skills
    assert "Data Analyst" in result.summary
    assert result.missing_foundational_knowledge
    assert result.transitional_roles
    assert any("completed" in caution for caution in result.cautions)


def test_outreach_endpoint_persists_generated_output() -> None:
    settings = Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    fake = FakeSupabaseClient(
        settings=settings,
        profile={"id": TEST_PROFILE_ID, "version": 1, "normalized_json": normalized_profile()},
        job_description={"id": TEST_JOB_ID, "structured_json": structured_job()},
    )
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/outreach-message-pack",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["output_type"] == "ai_outreach_message_pack"
    assert fake.generated_outputs[0]["output_type"] == "ai_outreach_message_pack"
    assert "LinkedIn Connection Message" in fake.generated_outputs[0]["result_markdown"]


def test_career_transition_endpoint_returns_cached_output() -> None:
    settings = Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    cached = generate_career_transition_analysis(
        build_career_transition_context(
            normalized_profile=normalized_profile(),
            readiness=build_readiness_dashboard(normalized_profile(), structured_job()),
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/career-transition-analysis",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert fake.generated_outputs == []
