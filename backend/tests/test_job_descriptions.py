from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from docx import Document
from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.jobs.job_parser import parse_job_description
from app.main import create_app
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    owns_profile: bool = True
    job_descriptions: list[dict[str, Any]] = field(default_factory=list)

    def profile_belongs_to_user(self, profile_id: str, user_id: str) -> bool:
        return self.owns_profile and profile_id == TEST_PROFILE_ID and user_id == TEST_USER_ID

    def create_job_description(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "job-id", **payload}
        self.job_descriptions.append(row)
        return row

    def list_job_descriptions(self, profile_id: str, user_id: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self.job_descriptions
            if row["profile_id"] == profile_id and row["user_id"] == user_id
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


def sample_job_text() -> str:
    return """
Senior Operations Analyst
Company: Acme Logistics
Responsibilities:
- Lead weekly operations reporting for regional teams.
- Coordinate stakeholder communication and process improvements.
Requirements:
- 3+ years of operations analytics experience.
- Strong Excel, SQL, project management, and communication skills.
Preferred Qualifications:
- Experience with Tableau and stakeholder management.
Education:
- Bachelor degree in business, analytics, or related field.
"""


def make_docx(text: str) -> bytes:
    buffer = BytesIO()
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(buffer)
    return buffer.getvalue()


def test_parse_job_description_extracts_structured_requirements() -> None:
    result = parse_job_description(sample_job_text())

    assert result.title == "Senior Operations Analyst"
    assert result.company == "Acme Logistics"
    assert "excel" in result.required_skills
    assert "sql" in result.required_skills
    assert "tableau" in result.tools
    assert "3+ years of operations analytics experience" in result.experience_requirements
    assert result.seniority == "senior"


def test_parse_job_description_extracts_broader_skill_taxonomy() -> None:
    result = parse_job_description(
        """
Healthcare Administrative Assistant
Requirements:
- Patient care coordination, medical billing, scheduling, and documentation.
- Strong customer service, attention to detail, and conflict resolution.
Preferred Qualifications:
- Experience with data entry, compliance, and Microsoft Office.
"""
    )

    assert "patient care" in result.required_skills
    assert "medical billing" in result.required_skills
    assert "documentation" in result.required_skills
    assert "microsoft office" in result.tools
    assert "attention to detail" in result.soft_skills


def test_create_job_description_from_text_persists_structured_result() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/job-descriptions",
        json={"text": sample_job_text()},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "job-id"
    assert body["source_type"] == "pasted_text"
    assert body["structured"]["company"] == "Acme Logistics"
    assert fake.job_descriptions[0]["structured_json"]["seniority"] == "senior"


def test_list_job_descriptions_returns_saved_targets() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)
    client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/job-descriptions",
        json={"text": sample_job_text()},
    )

    response = client.get(f"/api/v1/profiles/{TEST_PROFILE_ID}/job-descriptions")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == "job-id"
    assert body[0]["structured"]["title"] == "Senior Operations Analyst"


def test_create_job_description_rejects_unowned_profile() -> None:
    fake = FakeSupabaseClient(owns_profile=False)
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/job-descriptions",
        json={"text": sample_job_text()},
    )

    assert response.status_code == 404


def test_create_job_description_from_docx_upload() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/job-descriptions/upload",
        files={
            "file": (
                "job.docx",
                make_docx(sample_job_text()),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "uploaded_docx"
    assert "project management" in body["structured"]["required_skills"]
