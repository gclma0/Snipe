from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.analysis.resume_quality import analyze_resume_quality
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
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


def normalized_profile() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "contact": {"emails": ["candidate@example.com"], "phones": ["555-123-4567"], "links": []},
        "sections": {
            "summary": "Finance analyst with experience in budgeting and reporting.",
            "experience": "Led monthly budget reporting for 12 department leaders.",
            "skills": "Excel, budgeting, communication",
            "education": "BS Finance",
        },
        "skills": [
            {"name": "excel"},
            {"name": "budgeting"},
            {"name": "communication"},
        ],
    }


def test_resume_quality_score_rewards_complete_profile() -> None:
    result = analyze_resume_quality(normalized_profile())

    assert result.score >= 90
    assert result.checks["has_email"] is True
    assert result.checks["has_experience_section"] is True
    assert not [finding for finding in result.findings if finding.severity == "high"]


def test_resume_quality_flags_missing_core_sections() -> None:
    result = analyze_resume_quality({"contact": {}, "sections": {}, "skills": []})

    codes = {finding.code for finding in result.findings}
    assert result.score < 50
    assert {"missing_email", "missing_experience", "missing_skills"}.issubset(codes)


def test_resume_quality_endpoint_persists_analysis() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 3,
            "normalized_json": normalized_profile(),
        }
    )
    client = client_with_fake_supabase(fake)

    response = client.post(f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/resume-quality")

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_type"] == "resume_quality"
    assert body["score"] >= 90
    assert fake.analyses[0]["profile_version"] == 3
    assert fake.analyses[0]["result_json"]["score"] == body["score"]


def test_resume_quality_endpoint_requires_normalized_profile() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 1,
            "normalized_json": {},
        }
    )
    client = client_with_fake_supabase(fake)

    response = client.post(f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/resume-quality")

    assert response.status_code == 409
