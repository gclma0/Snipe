from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

import fitz
import jwt
from docx import Document
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
    owns_profile: bool = True
    uploaded: list[dict[str, Any]] = field(default_factory=list)
    deleted_storage: list[str] = field(default_factory=list)
    source_delete_markers: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    profiles: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def profile_belongs_to_user(self, profile_id: str, user_id: str) -> bool:
        return self.owns_profile and profile_id == TEST_PROFILE_ID and user_id == TEST_USER_ID

    def upload_document(self, path: str, content: bytes, content_type: str) -> None:
        self.uploaded.append(
            {
                "path": path,
                "content": content,
                "content_type": content_type,
            }
        )

    def delete_storage_objects(self, paths: list[str]) -> None:
        self.deleted_storage.extend(paths)

    def mark_profile_source_document_deleted(
        self,
        *,
        source_id: str,
        profile_id: str,
        user_id: str,
        deleted_at: str,
    ) -> dict[str, Any]:
        marker = {
            "source_id": source_id,
            "profile_id": profile_id,
            "user_id": user_id,
            "deleted_at": deleted_at,
        }
        self.source_delete_markers.append(marker)
        return marker

    def create_profile_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "source-id", **payload}
        self.sources.append(row)
        return row

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if not self.profile_belongs_to_user(profile_id, user_id):
            return None
        return {"id": profile_id, "user_id": user_id, "version": 1, "normalized_json": {}}

    def update_candidate_profile(
        self,
        *,
        profile_id: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        row = {"id": profile_id, "user_id": user_id, **payload}
        self.profiles.append(row)
        return row

    def create_profile_evidence(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.evidence.extend(payloads)
        return payloads


def make_pdf(text: str = "Backend Developer") -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def make_docx(text: str = "Finance Analyst") -> bytes:
    buffer = BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def make_token() -> str:
    return jwt.encode(
        {"aud": "authenticated", "sub": TEST_USER_ID, "email": "user@example.com"},
        TEST_SECRET,
        algorithm="HS256",
    )


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


def test_resume_upload_requires_authentication() -> None:
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET))
    client = TestClient(app)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/resume",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
    )

    assert response.status_code == 401


def test_resume_upload_rejects_unsupported_file_type() -> None:
    client = client_with_fake_supabase(FakeSupabaseClient())

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/resume",
        files={"file": ("resume.txt", b"plain text", "text/plain")},
        headers={"Authorization": f"Bearer {make_token()}"},
    )

    assert response.status_code == 415


def test_resume_upload_rejects_missing_profile_ownership() -> None:
    client = client_with_fake_supabase(FakeSupabaseClient(owns_profile=False))

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/resume",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        headers={"Authorization": f"Bearer {make_token()}"},
    )

    assert response.status_code == 404


def test_resume_upload_parses_uploads_and_records_pdf_source() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/resume",
        files={
            "file": (
                "resume.pdf",
                make_pdf("Summary\nQA Automation\nSkills\nPython, project management"),
                "application/pdf",
            )
        },
        headers={"Authorization": f"Bearer {make_token()}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_id"] == "source-id"
    assert body["source_type"] == "resume_pdf"
    assert body["status"] == "parsed"
    assert body["page_count"] == 1
    assert body["storage_path"] == f"{TEST_USER_ID}/{TEST_PROFILE_ID}/resume.pdf"
    assert body["normalized_profile_updated"] is True
    assert body["profile_version"] == 2
    assert fake.uploaded[0]["path"] == body["storage_path"]
    assert fake.sources[0]["content_hash"] == body["content_hash"]
    assert fake.profiles[0]["normalized_json"]["schema_version"] == 1
    assert fake.evidence


def test_resume_upload_parses_uploads_and_records_docx_source() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/resume",
        files={
            "file": (
                "resume.docx",
                make_docx("Marketing Specialist"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers={"Authorization": f"Bearer {make_token()}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "resume_docx"
    assert body["paragraph_count"] == 1


def test_resume_upload_can_delete_raw_document_after_parsing() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/sources/resume",
        files={
            "file": (
                "resume.pdf",
                make_pdf("Summary\nOperations Analyst\nSkills\nExcel, SQL"),
                "application/pdf",
            )
        },
        data={"delete_after_parsing": "true"},
        headers={"Authorization": f"Bearer {make_token()}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["delete_after_parsing"] is True
    assert body["raw_document_retained"] is False
    assert fake.deleted_storage == [body["storage_path"]]
    assert fake.sources[0]["delete_after_parsing"] is True
    assert fake.sources[0]["retention_policy"] == "delete_after_parsing"
    assert fake.source_delete_markers[0]["source_id"] == "source-id"
