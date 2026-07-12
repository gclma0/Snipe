from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.reports.report_builder import build_basic_report
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_JOB_ID = "22222222-2222-2222-2222-222222222222"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None
    job_description: dict[str, Any] | None = None
    outputs: list[dict[str, Any]] = field(default_factory=list)

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

    def create_generated_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "output-id", **payload}
        self.outputs.append(row)
        return row


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
        "schema_version": 1,
        "sources": [{"source_id": "source-id"}],
        "contact": {"emails": ["candidate@example.com"], "phones": ["555-123-4567"]},
        "sections": {
            "summary": "Senior operations analyst focused on reporting and stakeholder management.",
            "experience": "Led weekly operations reviews for 15 stakeholders.",
            "skills": "Excel, SQL, operations, project management, stakeholder management",
            "education": "Bachelor degree in business.",
        },
        "skills": [
            {"name": "excel", "source": "resume"},
            {"name": "sql", "source": "resume"},
            {"name": "operations", "source": "resume"},
            {"name": "project management", "source": "resume"},
            {"name": "stakeholder management", "source": "resume"},
        ],
    }


def structured_job() -> dict[str, Any]:
    return {
        "required_skills": ["Excel", "SQL", "project management"],
        "preferred_skills": ["stakeholder management"],
        "tools": [],
        "soft_skills": ["communication"],
    }


def test_build_basic_report_contains_scores_strengths_and_markdown() -> None:
    result = build_basic_report(normalized_profile(), structured_job())

    assert result.report_type == "mvp_basic_report"
    assert result.readiness.scores.overall > 0
    assert result.strengths
    assert "# Snipe Career Report" in result.markdown
    assert "## Skill Gaps" in result.markdown


def test_basic_report_endpoint_persists_generated_output() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 7,
            "normalized_json": normalized_profile(),
        },
        job_description={
            "id": TEST_JOB_ID,
            "profile_id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "structured_json": structured_job(),
        },
    )
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/reports/basic",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["report_type"] == "mvp_basic_report"
    assert fake.outputs[0]["output_type"] == "mvp_basic_report"
    assert fake.outputs[0]["provider"] == "deterministic"
    assert fake.outputs[0]["result_markdown"].startswith("# Snipe Career Report")


def test_basic_report_endpoint_requires_normalized_profile() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 1,
            "normalized_json": {},
        }
    )
    client = client_with_fake_supabase(fake)

    response = client.post(f"/api/v1/profiles/{TEST_PROFILE_ID}/reports/basic")

    assert response.status_code == 409
