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
    fail_summary: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)

    def create_usage_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.fail:
            raise SupabaseError("simulated usage insert failure", operation="usage_event_insert")
        event = {"id": "usage-event-1", **payload}
        self.events.append(event)
        return event

    def list_usage_events_for_summary(self, *, since_iso: str, limit: int = 1000) -> list[dict[str, Any]]:
        if self.fail_summary:
            raise SupabaseError("simulated usage summary failure", operation="usage_event_summary")
        assert since_iso
        return self.events[:limit]


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


def test_usage_summary_returns_aggregate_counts_without_event_rows() -> None:
    fake = FakeSupabaseClient(
        events=[
            {"event_name": "production_smoke_test_ran", "surface": "system_panel"},
            {"event_name": "system_diagnostics_checked", "surface": "system_panel"},
            {"event_name": "system_diagnostics_checked", "surface": "system_panel"},
            {"event_name": "resume_uploaded", "surface": "resume_workflow"},
        ]
    )
    client = client_with_fake_supabase(fake)

    response = client.get("/api/v1/usage/summary?days=14")

    assert response.status_code == 200
    assert response.json() == {
        "days": 14,
        "total_events": 4,
        "event_counts": [
            {"name": "system_diagnostics_checked", "count": 2},
            {"name": "production_smoke_test_ran", "count": 1},
            {"name": "resume_uploaded", "count": 1},
        ],
        "surface_counts": [
            {"name": "system_panel", "count": 3},
            {"name": "resume_workflow", "count": 1},
        ],
    }


def test_usage_summary_reports_supabase_failures() -> None:
    client = client_with_fake_supabase(FakeSupabaseClient(fail_summary=True))

    response = client.get("/api/v1/usage/summary")

    assert response.status_code == 502
    assert response.json()["detail"] == "Supabase usage_event_summary failed."
