from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.matching.skill_gap import analyze_skill_gap
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_JOB_ID = "22222222-2222-2222-2222-222222222222"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None
    job_description: dict[str, Any] | None
    analyses: list[dict[str, Any]] = field(default_factory=list)

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
        "skills": [
            {"name": "Excel", "source": "resume"},
            {"name": "SQL", "source": "resume"},
            {"name": "communication", "source": "resume"},
            {"name": "operations", "source": "resume"},
        ],
    }


def structured_job() -> dict[str, Any]:
    return {
        "required_skills": ["Excel", "project management", "stakeholder management"],
        "preferred_skills": ["SQL"],
        "tools": ["Tableau"],
        "soft_skills": ["communication"],
    }


def test_skill_gap_categorizes_match_missing_and_transferable_skills() -> None:
    result = analyze_skill_gap(normalized_profile(), structured_job())

    matched = {item.skill for item in result.matched_skills}
    missing = {item.skill for item in result.missing_skills}
    transferable = {item.skill for item in result.transferable_skills}
    assert {"excel", "sql", "communication"}.issubset(matched)
    assert {"project management", "stakeholder management", "tableau"}.issubset(missing)
    assert "operations" in transferable
    assert result.score > 0


def test_skill_gap_endpoint_persists_analysis() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 5,
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/skill-gap",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["analysis_type"] == "skill_gap"
    assert fake.analyses[0]["job_description_id"] == TEST_JOB_ID
    assert fake.analyses[0]["profile_version"] == 5


def test_skill_gap_endpoint_requires_existing_job_description() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 1,
            "normalized_json": normalized_profile(),
        },
        job_description=None,
    )
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/skill-gap",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 404


def test_skill_gap_endpoint_requires_normalized_profile() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 1,
            "normalized_json": {},
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/analyses/skill-gap",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 409
