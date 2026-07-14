from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.supabase.client import SupabaseError
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    owns_profile: bool = True
    storage_paths: list[str] = field(default_factory=lambda: ["user/profile/resume.pdf"])
    fail_operation: str | None = None
    deleted_storage: list[str] = field(default_factory=list)
    deleted_profiles: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=lambda: [{"id": "output-1"}])
    events: list[dict[str, Any]] = field(default_factory=list)
    profile: dict[str, Any] = field(
        default_factory=lambda: {
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "career_goal": "Prepare for a target role",
            "preferred_role": "Operations Analyst",
            "normalized_json": {"skills": [{"name": "excel"}]},
        }
    )
    sources: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "id": "source-1",
                "source_type": "resume",
                "storage_path": "user/profile/resume.pdf",
                "original_filename": "resume.pdf",
                "content_hash": "content-hash",
            }
        ]
    )
    evidence: list[dict[str, Any]] = field(
        default_factory=lambda: [{"id": "evidence-1", "fact_type": "skill", "fact_key": "excel"}]
    )
    job_descriptions: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "id": "job-1",
                "source_type": "pasted_text",
                "raw_text": "Sensitive pasted job text",
                "structured_json": {"title": "Operations Analyst"},
            }
        ]
    )
    analyses: list[dict[str, Any]] = field(
        default_factory=lambda: [{"id": "analysis-1", "analysis_type": "resume_quality"}]
    )

    def profile_belongs_to_user(self, profile_id: str, user_id: str) -> bool:
        return self.owns_profile and profile_id == TEST_PROFILE_ID and user_id == TEST_USER_ID

    def list_profile_storage_paths(self, profile_id: str, user_id: str) -> list[str]:
        assert profile_id == TEST_PROFILE_ID
        assert user_id == TEST_USER_ID
        return self.storage_paths

    def delete_storage_objects(self, paths: list[str]) -> None:
        if self.fail_operation == "storage_delete":
            raise SupabaseError("simulated storage delete failure", operation="storage_delete")
        self.deleted_storage.extend(paths)

    def delete_candidate_profile(self, profile_id: str, user_id: str) -> bool:
        if self.fail_operation == "profile_delete":
            raise SupabaseError("simulated profile delete failure", operation="profile_delete")
        self.deleted_profiles.append({"profile_id": profile_id, "user_id": user_id})
        return True

    def list_generated_outputs(
        self,
        *,
        user_id: str,
        profile_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        assert profile_id == TEST_PROFILE_ID
        assert user_id == TEST_USER_ID
        return self.outputs[:limit]

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if not self.profile_belongs_to_user(profile_id, user_id):
            return None
        return self.profile

    def list_profile_sources(self, profile_id: str, user_id: str) -> list[dict[str, Any]]:
        assert profile_id == TEST_PROFILE_ID
        assert user_id == TEST_USER_ID
        return self.sources

    def list_profile_evidence(self, profile_id: str) -> list[dict[str, Any]]:
        assert profile_id == TEST_PROFILE_ID
        return self.evidence

    def list_job_descriptions(
        self,
        *,
        profile_id: str,
        user_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        assert profile_id == TEST_PROFILE_ID
        assert user_id == TEST_USER_ID
        return self.job_descriptions[:limit]

    def list_profile_analyses(
        self,
        *,
        user_id: str,
        profile_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        assert profile_id == TEST_PROFILE_ID
        assert user_id == TEST_USER_ID
        return self.analyses[:limit]

    def create_privacy_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "id": f"event-{len(self.events) + 1}",
            "created_at": "2026-07-14T00:00:00Z",
            **payload,
        }
        self.events.insert(0, event)
        return event

    def list_privacy_events(
        self,
        *,
        user_id: str,
        profile_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        assert profile_id == TEST_PROFILE_ID
        assert user_id == TEST_USER_ID
        return [
            {
                "id": event.get("id"),
                "event_type": event.get("event_type"),
                "metadata": event.get("metadata", {}),
                "created_at": event.get("created_at"),
            }
            for event in self.events[:limit]
        ]


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


def test_delete_profile_data_deletes_storage_then_profile() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.delete(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy")

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] is True
    assert body["deleted_storage_objects"] == 1
    assert fake.deleted_storage == ["user/profile/resume.pdf"]
    assert fake.deleted_profiles == [{"profile_id": TEST_PROFILE_ID, "user_id": TEST_USER_ID}]


def test_data_summary_reports_documents_outputs_and_retention() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy/data-summary")

    assert response.status_code == 200
    body = response.json()
    assert body["profile_exists"] is True
    assert body["stored_document_count"] == 1
    assert body["generated_output_count"] == 1
    assert body["privacy_event_count"] == 0
    assert "private" in body["retention_policy"].lower()
    assert fake.events[0]["event_type"] == "privacy_summary_viewed"


def test_export_profile_data_returns_structured_data_without_raw_job_text() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy/export")

    assert response.status_code == 200
    body = response.json()
    assert body["export_version"] == "profile-data-export-v1"
    assert body["includes_raw_document_files"] is False
    assert body["profile"]["id"] == TEST_PROFILE_ID
    assert body["sources"][0]["source_type"] == "resume"
    assert body["evidence"][0]["fact_key"] == "excel"
    assert body["job_descriptions"][0]["structured_json"]["title"] == "Operations Analyst"
    assert "raw_text" not in body["job_descriptions"][0]
    assert body["analyses"][0]["analysis_type"] == "resume_quality"
    assert fake.events[0]["event_type"] == "profile_data_exported"


def test_list_privacy_events_returns_audit_trail() -> None:
    fake = FakeSupabaseClient(
        events=[
            {
                "id": "event-1",
                "event_type": "profile_documents_deleted",
                "metadata": {"deleted_storage_objects": 1},
                "created_at": "2026-07-14T00:00:00Z",
            }
        ]
    )
    client = client_with_fake_supabase(fake)

    response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy/events")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["event_type"] == "profile_documents_deleted"
    assert body[0]["metadata"]["deleted_storage_objects"] == 1


def test_delete_documents_keeps_profile() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.delete(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy/documents")

    assert response.status_code == 200
    assert response.json()["profile_retained"] is True
    assert response.json()["deleted_storage_objects"] == 1
    assert fake.deleted_storage == ["user/profile/resume.pdf"]
    assert fake.deleted_profiles == []
    assert fake.events[0]["event_type"] == "profile_documents_deleted"


def test_delete_profile_data_rejects_unowned_profile() -> None:
    fake = FakeSupabaseClient(owns_profile=False)
    client = client_with_fake_supabase(fake)

    response = client.delete(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy")

    assert response.status_code == 404
    assert fake.deleted_storage == []
    assert fake.deleted_profiles == []


def test_delete_profile_data_handles_missing_storage_paths() -> None:
    fake = FakeSupabaseClient(storage_paths=[])
    client = client_with_fake_supabase(fake)

    response = client.delete(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy")

    assert response.status_code == 200
    assert response.json()["deleted_storage_objects"] == 0
    assert fake.deleted_profiles == [{"profile_id": TEST_PROFILE_ID, "user_id": TEST_USER_ID}]
    assert fake.events[0]["event_type"] == "profile_data_deletion_requested"


def test_delete_profile_data_reports_failing_stage() -> None:
    fake = FakeSupabaseClient(fail_operation="storage_delete")
    client = client_with_fake_supabase(fake)

    response = client.delete(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy")

    assert response.status_code == 502
    assert response.json()["detail"] == "Supabase storage_delete failed."
