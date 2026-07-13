from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.matching.job_matcher import build_job_match_query, match_jobs_from_rag
from app.rag.schemas import RagCitation, RagSearchResult
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None
    rows: list[dict[str, Any]] = field(default_factory=list)
    analyses: list[dict[str, Any]] = field(default_factory=list)
    requested_limit: int | None = None

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def match_rag_chunks(
        self,
        *,
        user_id: str,
        query_embedding: list[float],
        source_types: list[str],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        assert user_id == TEST_USER_ID
        assert source_types == ["job_description", "job_listing"]
        assert query_embedding
        self.requested_limit = limit
        return self.rows[:limit]

    def create_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.analyses.append(payload)
        return {**payload, "id": "analysis-1"}


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


def normalized_profile() -> dict[str, Any]:
    return {
        "skills": [
            {"name": "python", "source": "resume"},
            {"name": "sql", "source": "resume"},
            {"name": "excel", "source": "resume"},
            {"name": "communication", "source": "resume"},
        ],
        "sections": {
            "summary": "Data analyst with Python, SQL, Excel, and dashboard reporting.",
            "experience": "Built SQL dashboards and Excel reports for stakeholder communication.",
        },
    }


def job_text(title: str, required: str, preferred: str = "") -> str:
    return f"""
{title}
Company: Example Co
Requirements
{required}
Preferred
{preferred}
Responsibilities
Build reports, collaborate with stakeholders, and improve workflows.
"""


def rag_result() -> RagSearchResult:
    return RagSearchResult(
        query="data analyst python sql",
        embedding_model="deterministic-hashing-v1",
        citations=[
            RagCitation(
                document_id="job-1",
                chunk_id="chunk-1",
                title="Data Analyst",
                source_type="job_listing",
                source_url="https://example.com/jobs/data",
                chunk_index=0,
                content=job_text("Data Analyst", "Python, SQL, Excel", "communication"),
                score=0.9,
            ),
            RagCitation(
                document_id="job-2",
                chunk_id="chunk-2",
                title="Frontend Engineer",
                source_type="job_listing",
                source_url="https://example.com/jobs/frontend",
                chunk_index=0,
                content=job_text("Frontend Engineer", "React, TypeScript, accessibility"),
                score=0.8,
            ),
        ],
    )


def test_job_matcher_ranks_by_deterministic_skill_alignment_before_semantic_score() -> None:
    result = match_jobs_from_rag(
        normalized_profile=normalized_profile(),
        rag_result=rag_result(),
        query="data analyst python sql",
    )

    assert result.matches[0].title == "Data Analyst"
    assert result.matches[0].match_score > result.matches[1].match_score
    assert result.matches[0].matched_skills == ["communication", "excel", "python", "sql"]
    assert result.matches[0].structured_job.title == "Data Analyst"
    assert "Python, SQL, Excel" in result.matches[0].source_excerpt
    assert "react" in result.matches[1].missing_skills
    assert result.checks["uses_deterministic_ranking"] is True


def test_job_matcher_explanations_are_evidence_bound() -> None:
    result = match_jobs_from_rag(
        normalized_profile=normalized_profile(),
        rag_result=rag_result(),
        query="data analyst python sql",
    )
    match = result.matches[0]

    assert match.citation.document_id == "job-1"
    assert match.citation.source_url == "https://example.com/jobs/data"
    assert "python" in match.explanation
    assert match.relevant_experience
    assert match.apply_recommendation == "strong_apply"


def test_build_job_match_query_uses_profile_without_raw_resume() -> None:
    query = build_job_match_query(normalized_profile(), fallback="Data Analyst")

    assert "Data Analyst" in query
    assert "python" in query
    assert len(query) <= 1000


def test_job_match_endpoint_returns_ranked_matches_and_persists_analysis() -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 3,
            "preferred_role": "Data Analyst",
            "normalized_json": normalized_profile(),
        },
        rows=[
            {
                "document_id": "job-1",
                "chunk_id": "chunk-1",
                "title": "Data Analyst",
                "source_type": "job_listing",
                "source_url": "https://example.com/jobs/data",
                "chunk_index": 0,
                "content": job_text("Data Analyst", "Python, SQL, Excel", "communication"),
                "score": 0.9,
                "metadata": {},
            }
        ],
    )
    client = client_with_fake_supabase(fake)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/job-matches",
        json={"query": "data analyst", "limit": 5},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["matches"][0]["title"] == "Data Analyst"
    assert body["matches"][0]["matched_skills"] == ["communication", "excel", "python", "sql"]
    assert body["matches"][0]["structured_job"]["title"] == "Data Analyst"
    assert "Python, SQL, Excel" in body["matches"][0]["source_excerpt"]
    assert fake.requested_limit == 5
    assert fake.analyses[0]["analysis_type"] == "job_match"
    assert fake.analyses[0]["profile_version"] == 3


def test_job_match_endpoint_requires_existing_normalized_profile() -> None:
    fake = FakeSupabaseClient(profile={"id": TEST_PROFILE_ID, "normalized_json": {}})
    client = client_with_fake_supabase(fake)

    response = client.post(f"/api/v1/profiles/{TEST_PROFILE_ID}/job-matches")

    assert response.status_code == 409
