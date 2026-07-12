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


def test_delete_profile_data_reports_failing_stage() -> None:
    fake = FakeSupabaseClient(fail_operation="storage_delete")
    client = client_with_fake_supabase(fake)

    response = client.delete(f"/api/v1/profiles/{TEST_PROFILE_ID}/privacy")

    assert response.status_code == 502
    assert response.json()["detail"] == "Supabase storage_delete failed."
