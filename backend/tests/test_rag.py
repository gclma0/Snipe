from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.rag.embeddings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
from app.rag.ingestion import chunk_text, ingest_rag_document
from app.rag.retrieval import build_rag_reference_context, rank_rag_rows, retrieve_rag_chunks
from app.rag.schemas import RagDocumentIngestion, RagSearchRequest
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


@dataclass
class FakeSupabaseClient:
    documents: list[dict[str, Any]] = field(default_factory=list)
    chunks: list[dict[str, Any]] = field(default_factory=list)
    matched_source_types: list[str] = field(default_factory=list)

    def create_rag_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {**payload, "id": f"doc-{len(self.documents) + 1}"}
        self.documents.append(row)
        return row

    def create_rag_chunks(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [
            {**payload, "id": f"chunk-{index + 1}"}
            for index, payload in enumerate(payloads, start=len(self.chunks))
        ]
        self.chunks.extend(rows)
        return rows

    def match_rag_chunks(
        self,
        *,
        user_id: str,
        query_embedding: list[float],
        source_types: list[str],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        assert user_id == TEST_USER_ID
        assert len(query_embedding) == EMBEDDING_DIMENSIONS
        self.matched_source_types = source_types
        rows = []
        for chunk in self.chunks:
            document = next(
                doc for doc in self.documents if doc["id"] == chunk["document_id"]
            )
            if source_types and document["source_type"] not in source_types:
                continue
            rows.append(
                {
                    "document_id": document["id"],
                    "chunk_id": chunk["id"],
                    "title": document["title"],
                    "source_type": document["source_type"],
                    "source_url": document.get("source_url"),
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "embedding": chunk["embedding"],
                    "metadata": chunk["metadata"],
                }
            )
        return rank_rag_rows(rows, query="python sql analytics", limit=limit)


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


def test_chunk_text_overlaps_and_embeds_chunks() -> None:
    text = " ".join(f"word{index}" for index in range(420))

    chunks = chunk_text(text, chunk_size_words=100, overlap_words=20)

    assert len(chunks) == 5
    assert chunks[0].token_count == 100
    assert chunks[1].metadata["word_start"] == 80
    assert len(chunks[0].embedding) == EMBEDDING_DIMENSIONS


def test_ingest_rag_document_stores_document_and_chunk_embeddings() -> None:
    fake = FakeSupabaseClient()
    document = RagDocumentIngestion(
        title="Data Analyst Role Framework",
        source_type="role_framework",
        text="Python SQL analytics dashboards stakeholder reporting " * 30,
        metadata={"role_family": "analytics"},
    )

    result = ingest_rag_document(document, user_id=TEST_USER_ID, supabase=fake)

    assert result.document_id == "doc-1"
    assert result.embedding_model == EMBEDDING_MODEL
    assert fake.documents[0]["metadata"] == {"role_family": "analytics"}
    assert fake.chunks
    assert fake.chunks[0]["document_id"] == "doc-1"
    assert len(fake.chunks[0]["embedding"]) == EMBEDDING_DIMENSIONS


def test_retrieve_rag_chunks_returns_ranked_citations() -> None:
    fake = FakeSupabaseClient()
    ingest_rag_document(
        RagDocumentIngestion(
            title="Analytics Guidance",
            source_type="career_guidance",
            text="Python SQL dashboards analytics stakeholder reporting " * 30,
        ),
        user_id=TEST_USER_ID,
        supabase=fake,
    )
    ingest_rag_document(
        RagDocumentIngestion(
            title="Design Guidance",
            source_type="career_guidance",
            text="Typography layout illustration brand identity portfolio " * 30,
        ),
        user_id=TEST_USER_ID,
        supabase=fake,
    )

    result = retrieve_rag_chunks(
        RagSearchRequest(query="python sql analytics", limit=2),
        user_id=TEST_USER_ID,
        supabase=fake,
    )

    assert result.citations[0].title == "Analytics Guidance"
    assert result.citations[0].score > 0
    assert result.citations[0].document_id == "doc-1"
    assert result.citations[0].chunk_id == "chunk-1"


def test_build_rag_reference_context_keeps_source_citations() -> None:
    fake = FakeSupabaseClient()
    ingest_rag_document(
        RagDocumentIngestion(
            title="Backend Job",
            source_type="job_listing",
            source_url="https://example.com/jobs/backend",
            text="FastAPI PostgreSQL API testing backend role " * 30,
        ),
        user_id=TEST_USER_ID,
        supabase=fake,
    )

    result = retrieve_rag_chunks(
        RagSearchRequest(query="backend api", limit=1),
        user_id=TEST_USER_ID,
        supabase=fake,
    )
    context = build_rag_reference_context(result)

    assert context == [
        {
            "title": "Backend Job",
            "source_type": "job_listing",
            "source_url": "https://example.com/jobs/backend",
            "content": result.citations[0].content,
            "score": result.citations[0].score,
            "metadata": result.citations[0].metadata,
        }
    ]


def test_rag_api_ingests_and_searches_documents() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)

    ingest_response = client.post(
        "/api/v1/rag/documents",
        json={
            "title": "Analytics Guidance",
            "source_type": "career_guidance",
            "text": "Python SQL analytics dashboards stakeholder reporting " * 30,
        },
    )
    search_response = client.post(
        "/api/v1/rag/search",
        json={"query": "python sql analytics", "limit": 1},
    )

    assert ingest_response.status_code == 201
    assert search_response.status_code == 200
    body = search_response.json()
    assert body["citations"][0]["title"] == "Analytics Guidance"
    assert body["citations"][0]["source_type"] == "career_guidance"


def test_job_reference_search_filters_to_job_sources() -> None:
    fake = FakeSupabaseClient()
    client = client_with_fake_supabase(fake)
    client.post(
        "/api/v1/rag/documents",
        json={
            "title": "Internal Job",
            "source_type": "job_listing",
            "text": "Python SQL analytics dashboards stakeholder reporting " * 30,
        },
    )

    response = client.post(
        "/api/v1/rag/jobs/search",
        json={"query": "python sql analytics", "source_types": ["career_guidance"], "limit": 1},
    )

    assert response.status_code == 200
    assert fake.matched_source_types == ["job_description", "job_listing"]
    assert response.json()["citations"][0]["source_type"] == "job_listing"
