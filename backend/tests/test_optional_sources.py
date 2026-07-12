from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.integrations.portfolio import PortfolioPage
from app.main import create_app
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


class FakePortfolioClient:
    def fetch_url(self, url: str) -> PortfolioPage:
        if "consultant" in url:
            return PortfolioPage(
                url=url,
                final_url="https://consultant.example",
                title="Operations Consultant",
                description="Client case study portfolio for operations strategy.",
                text=(
                    "Operations consultant portfolio with client case study results, "
                    "marketing strategy, sales enablement, and contact details."
                ),
                links=["/contact"],
            )
        return PortfolioPage(
            url=url,
            final_url="https://dev.example",
            title="Frontend Engineer Portfolio",
            description="Selected work across React, TypeScript, APIs, and testing.",
            text="Project case study for React TypeScript frontend testing and API automation.",
            links=["/work", "/contact"],
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
    uploads: list[dict[str, Any]] = field(default_factory=list)

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def create_profile_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": f"source-{len(self.sources) + 1}", **payload}
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

    def upload_document(self, *, path: str, content: bytes, content_type: str) -> None:
        self.uploads.append({"path": path, "content": content, "content_type": content_type})


def client_with_fake_supabase(fake: FakeSupabaseClient, monkeypatch) -> TestClient:
    import app.api.routes.source_portfolio as source_portfolio

    monkeypatch.setattr(source_portfolio, "PortfolioClient", FakePortfolioClient)
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET))
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="user@example.com",
        role="authenticated",
        claims={},
    )
    app.dependency_overrides[get_supabase_client] = lambda: fake
    return TestClient(app)


def test_add_portfolio_source_records_technical_signals(monkeypatch) -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/portfolio",
        json={"url": "https://dev.example"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Frontend Engineer Portfolio"
    assert "react" in body["technical_signals"]
    assert body["evidence_count"] >= 2
    assert fake.sources[0]["source_type"] == "portfolio_url"
    assert fake.updates[0]["normalized_json"]["optional_sources"]["portfolio"]["title"]


def test_add_portfolio_source_records_non_technical_signals(monkeypatch) -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/portfolio",
        json={"url": "https://consultant.example"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "operations" in body["non_technical_signals"]
    assert "marketing" in body["non_technical_signals"]
    assert body["project_signal_count"] > 0


def test_add_linkedin_text_source_records_optional_source(monkeypatch) -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake, monkeypatch)
    linkedin_text = """
    Senior Marketing Operations Manager
    About
    I lead marketing operations, analytics, sales alignment, and strategy.
    Experience
    Built campaign reporting process for regional sales teams.
    Skills
    Marketing
    Analytics
    Sales
    """

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/linkedin",
        json={"text": linkedin_text},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "linkedin_pasted_text"
    assert "marketing" in body["skill_signals"]
    assert body["experience_count"] > 0
    assert fake.sources[0]["source_type"] == "linkedin_pasted_text"
    assert fake.updates[0]["normalized_json"]["optional_sources"]["linkedin"]["headline"]


def test_linkedin_url_only_is_rejected_without_scraping(monkeypatch) -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/linkedin",
        json={"text": "https://www.linkedin.com/in/example-user/"},
    )

    assert response.status_code == 400
    assert "Direct LinkedIn scraping is not supported" in response.json()["detail"]
    assert fake.sources == []
