from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.scoring.ats import analyze_ats_readiness
from app.scoring.profile_completeness import analyze_profile_completeness
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None
    analyses: list[dict[str, Any]] = field(default_factory=list)

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def create_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "analysis-id", **payload}
        self.analyses.append(row)
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


def complete_profile() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sources": [{"source_id": "source-id", "source_type": "resume_pdf"}],
        "contact": {"emails": ["candidate@example.com"], "phones": ["555-123-4567"], "links": []},
        "sections": {
            "summary": "Operations leader with vendor management and reporting experience.",
            "experience": (
                "Led weekly operations reviews for 15 stakeholders and reduced delays by 12%."
            ),
            "skills": (
                "Excel, operations, project management, communication, stakeholder management"
            ),
            "education": "BA Business Administration",
        },
        "skills": [
            {"name": "excel"},
            {"name": "operations"},
            {"name": "project management"},
            {"name": "communication"},
            {"name": "stakeholder management"},
        ],
    }


def test_ats_readiness_scores_complete_profile_highly() -> None:
    result = analyze_ats_readiness(complete_profile())

    assert result.analysis_type == "ats_readiness"
    assert result.score >= 90
    assert result.checks["has_standard_sections"] is True


def test_profile_completeness_penalizes_missing_resume_source() -> None:
    profile = complete_profile()
    profile["sources"] = []

    result = analyze_profile_completeness(profile)

    assert result.score < 100
    assert any(finding.code == "profile_source_missing" for finding in result.findings)


def test_ats_readiness_endpoint_persists_analysis() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 4,
            "normalized_json": complete_profile(),
        }
    )
    client = client_with_fake_supabase(fake)

    response = client.post(f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/ats-readiness")

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_type"] == "ats_readiness"
    assert fake.analyses[0]["analysis_type"] == "ats_readiness"
    assert fake.analyses[0]["profile_version"] == 4


def test_profile_completeness_endpoint_persists_analysis() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 2,
            "normalized_json": complete_profile(),
        }
    )
    client = client_with_fake_supabase(fake)

    response = client.post(f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/profile-completeness")

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_type"] == "profile_completeness"
    assert fake.analyses[0]["analysis_type"] == "profile_completeness"


def test_ats_readiness_wording_does_not_claim_vendor_guarantee() -> None:
    result = analyze_ats_readiness({"contact": {}, "sections": {}, "skills": []})
    text = result.model_dump_json().lower()

    assert "guarantee" not in text
    assert "commercial ats" not in text
