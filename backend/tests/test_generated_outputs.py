from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

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
    outputs: list[dict[str, Any]] = field(default_factory=list)
    requested_limit: int | None = None
    requested_output_id: str | None = None
    deleted_output_id: str | None = None

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def list_generated_outputs(
        self,
        *,
        user_id: str,
        profile_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        assert user_id == TEST_USER_ID
        assert profile_id == TEST_PROFILE_ID
        self.requested_limit = limit
        return self.outputs

    def get_generated_output_by_id(
        self,
        *,
        user_id: str,
        profile_id: str,
        output_id: str,
    ) -> dict[str, Any] | None:
        assert user_id == TEST_USER_ID
        assert profile_id == TEST_PROFILE_ID
        self.requested_output_id = output_id
        return next((output for output in self.outputs if output["id"] == output_id), None)

    def delete_generated_output(
        self,
        *,
        user_id: str,
        profile_id: str,
        output_id: str,
    ) -> bool:
        assert user_id == TEST_USER_ID
        assert profile_id == TEST_PROFILE_ID
        self.deleted_output_id = output_id
        before_count = len(self.outputs)
        self.outputs = [output for output in self.outputs if output["id"] != output_id]
        return len(self.outputs) != before_count


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


def test_generated_outputs_endpoint_lists_profile_outputs() -> None:
    fake = FakeSupabaseClient(
        profile={"id": TEST_PROFILE_ID, "user_id": TEST_USER_ID},
        outputs=[
            {
                "id": "output-1",
                "output_type": "ai_interview_prep",
                "job_description_id": None,
                "prompt_version": "ai-interview-prep-v1",
                "provider": "local_template",
                "model_name": "local-template-v1",
                "result_json": {"summary": "Interview prep summary."},
                "result_markdown": "# Snipe Interview Prep",
                "status": "completed",
                "created_at": "2026-07-13T12:00:00Z",
            }
        ],
    )
    client = client_with_fake_supabase(fake)

    response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/generated-outputs?limit=10")

    assert response.status_code == 200
    assert fake.requested_limit == 10
    body = response.json()
    assert body[0]["output_type"] == "ai_interview_prep"
    assert body[0]["result_json"]["summary"] == "Interview prep summary."


def test_generated_outputs_endpoint_requires_existing_profile() -> None:
    fake = FakeSupabaseClient(profile=None)
    client = client_with_fake_supabase(fake)

    response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/generated-outputs")

    assert response.status_code == 404


def test_generated_outputs_endpoint_gets_single_output() -> None:
    fake = FakeSupabaseClient(
        profile={"id": TEST_PROFILE_ID, "user_id": TEST_USER_ID},
        outputs=[
            {
                "id": "output-1",
                "output_type": "ai_application_materials",
                "job_description_id": None,
                "prompt_version": "ai-application-materials-v1",
                "provider": "local_template",
                "model_name": "local-template-v1",
                "result_json": {"summary": "Application materials summary."},
                "result_markdown": "# Snipe Application Materials",
                "status": "completed",
                "created_at": "2026-07-13T12:00:00Z",
            }
        ],
    )
    client = client_with_fake_supabase(fake)

    response = client.get(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/generated-outputs/output-1",
    )

    assert response.status_code == 200
    assert fake.requested_output_id == "output-1"
    assert response.json()["result_json"]["summary"] == "Application materials summary."


def test_generated_outputs_endpoint_hides_missing_or_wrong_user_output() -> None:
    fake = FakeSupabaseClient(
        profile={"id": TEST_PROFILE_ID, "user_id": TEST_USER_ID},
        outputs=[],
    )
    client = client_with_fake_supabase(fake)

    response = client.get(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/generated-outputs/other-output",
    )

    assert response.status_code == 404


def test_generated_outputs_endpoint_deletes_single_output() -> None:
    fake = FakeSupabaseClient(
        profile={"id": TEST_PROFILE_ID, "user_id": TEST_USER_ID},
        outputs=[
            {
                "id": "output-1",
                "output_type": "ai_interview_prep",
                "job_description_id": None,
                "prompt_version": "ai-interview-prep-v1",
                "provider": "local_template",
                "model_name": "local-template-v1",
                "result_json": {"summary": "Interview prep summary."},
                "result_markdown": "# Snipe Interview Prep",
                "status": "completed",
                "created_at": "2026-07-13T12:00:00Z",
            }
        ],
    )
    client = client_with_fake_supabase(fake)

    response = client.delete(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/generated-outputs/output-1",
    )

    assert response.status_code == 200
    assert response.json() == {"output_id": "output-1", "deleted": True}
    assert fake.deleted_output_id == "output-1"
    assert fake.outputs == []


def test_generated_outputs_endpoint_returns_404_for_delete_miss() -> None:
    fake = FakeSupabaseClient(
        profile={"id": TEST_PROFILE_ID, "user_id": TEST_USER_ID},
        outputs=[],
    )
    client = client_with_fake_supabase(fake)

    response = client.delete(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/generated-outputs/missing-output",
    )

    assert response.status_code == 404
