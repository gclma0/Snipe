from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.integrations.github import GitHubProfile, GitHubRepository
from app.main import create_app
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


class FakeGitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def fetch_public_profile(self, username_or_url: str) -> GitHubProfile:
        assert username_or_url == "octocat"
        return GitHubProfile(
            username="octocat",
            html_url="https://github.com/octocat",
            name="Octocat",
            bio="Example profile",
            public_repos=2,
            followers=10,
            repositories=[
                GitHubRepository(
                    name="hello-world",
                    full_name="octocat/hello-world",
                    html_url="https://github.com/octocat/hello-world",
                    language="Python",
                    stargazers_count=5,
                    forks_count=1,
                    archived=False,
                    fork=False,
                    pushed_at="2026-01-01T00:00:00Z",
                    has_readme=True,
                    has_tests=True,
                    has_ci=True,
                )
            ],
        )


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None = field(
        default_factory=lambda: {
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 2,
            "normalized_json": {"schema_version": 1},
        }
    )
    sources: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def create_profile_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "source-id", **payload}
        self.sources.append(row)
        return row

    def create_profile_evidence(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.evidence.extend(payloads)
        return payloads

    def update_candidate_profile(
        self,
        *,
        profile_id: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        row = {"id": profile_id, "user_id": user_id, **payload}
        self.updates.append(row)
        return row


def client_with_fake_supabase(fake: FakeSupabaseClient, monkeypatch) -> TestClient:
    import app.api.routes.source_github as source_github

    monkeypatch.setattr(source_github, "GitHubClient", FakeGitHubClient)
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET))
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="user@example.com",
        role="authenticated",
        claims={},
    )
    app.dependency_overrides[get_supabase_client] = lambda: fake
    return TestClient(app)


def test_add_github_source_records_optional_source_and_evidence(monkeypatch) -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/github",
        json={"username_or_url": "octocat"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "octocat"
    assert body["primary_languages"] == ["Python"]
    assert body["evidence_count"] == 2
    assert fake.sources[0]["source_type"] == "github_public"
    assert fake.updates[0]["version"] == 3
    assert fake.updates[0]["normalized_json"]["optional_sources"]["github"]["username"] == "octocat"


def test_add_github_source_rejects_missing_profile(monkeypatch) -> None:
    fake = FakeSupabaseClient(profile=None)
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/github",
        json={"username_or_url": "octocat"},
    )

    assert response.status_code == 404
