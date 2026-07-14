from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.supabase.client import SupabaseError
from app.supabase.dependencies import get_supabase_client


@dataclass
class FakeSupabaseClient:
    fail: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)

    def create_usage_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.fail:
            raise SupabaseError("simulated usage insert failure", operation="usage_event_insert")
        event = {"id": "usage-event-1", **payload}
        self.events.append(event)
        return event


def client_with_fake_supabase(fake: FakeSupabaseClient) -> TestClient:
    app = create_app(Settings(supabase_url=None))
    app.dependency_overrides[get_supabase_client] = lambda: fake
    return TestClient(app)


def test_usage_event_accepts_anonymous_non_content_metadata() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        "/api/v1/usage/events",
        json={
            "anonymous_session_id": "session-123456",
            "event_name": "ai_provider_checked",
            "surface": "system_panel",
            "path": "/dashboard?token=should-not-persist",
            "metadata": {
                "configured": True,
                "mode": "external",
                "resume_text": "Sensitive resume content",
                "job_text": "Sensitive job text",
                "api_key": "secret",
                "profile_id": "profile-1",
                "count": 2,
                "nested": {"not": "stored"},
            },
        },
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": True, "event_name": "ai_provider_checked"}
    assert fake.events == [
        {
            "id": "usage-event-1",
            "anonymous_session_id": "session-123456",
            "event_name": "ai_provider_checked",
            "surface": "system_panel",
            "path": "/dashboard",
            "metadata": {
                "configured": True,
                "mode": "external",
                "count": 2,
            },
        }
    ]


def test_usage_event_rejects_invalid_event_names_before_storage() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        "/api/v1/usage/events",
        json={
            "anonymous_session_id": "session-123456",
            "event_name": "AI Provider Checked",
            "surface": "system_panel",
            "metadata": {},
        },
    )

    assert response.status_code == 422
    assert fake.events == []


def test_usage_event_reports_supabase_failures() -> None:
    client = client_with_fake_supabase(FakeSupabaseClient(fail=True))

    response = client.post(
        "/api/v1/usage/events",
        json={
            "anonymous_session_id": "session-123456",
            "event_name": "ai_provider_checked",
            "surface": "system_panel",
            "metadata": {},
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Supabase usage_event_insert failed."
