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
    sources: list[dict[str, Any]] = field(default_factory=list)

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

    def create_profile_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "source-id", **payload}
        self.sources.append(row)
        return row


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
        files={"file": ("resume.pdf", make_pdf("QA Automation"), "application/pdf")},
        headers={"Authorization": f"Bearer {make_token()}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_id"] == "source-id"
    assert body["source_type"] == "resume_pdf"
    assert body["status"] == "parsed"
    assert body["page_count"] == 1
    assert body["storage_path"] == f"{TEST_USER_ID}/{TEST_PROFILE_ID}/resume.pdf"
    assert fake.uploaded[0]["path"] == body["storage_path"]
    assert fake.sources[0]["content_hash"] == body["content_hash"]


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
