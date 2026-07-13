from typing import Any

from app.rag.embeddings import EMBEDDING_MODEL, cosine_similarity, embed_text
from app.rag.schemas import RagCitation, RagSearchRequest, RagSearchResult


def retrieve_rag_chunks(
    request: RagSearchRequest,
    *,
    user_id: str,
    supabase: Any,
) -> RagSearchResult:
    query_embedding = embed_text(request.query)
    rows = supabase.match_rag_chunks(
        user_id=user_id,
        query_embedding=query_embedding,
        source_types=request.source_types,
        limit=request.limit,
    )
    citations = [_citation_from_row(row) for row in rows]
    return RagSearchResult(
        query=request.query,
        embedding_model=EMBEDDING_MODEL,
        citations=citations[: request.limit],
    )


def rank_rag_rows(
    rows: list[dict[str, Any]],
    *,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    query_embedding = embed_text(query)
    scored_rows = []
    for row in rows:
        embedding = row.get("embedding")
        score = (
            cosine_similarity(query_embedding, embedding)
            if isinstance(embedding, list)
            else _lexical_score(query, str(row.get("content") or ""))
        )
        scored_rows.append({**row, "score": max(0.0, min(1.0, score))})
    scored_rows.sort(key=lambda row: row["score"], reverse=True)
    return scored_rows[:limit]


def build_rag_reference_context(
    result: RagSearchResult,
    *,
    max_citations: int = 5,
) -> list[dict[str, Any]]:
    return [
        {
            "title": citation.title,
            "source_type": citation.source_type,
            "source_url": citation.source_url,
            "content": citation.content,
            "score": citation.score,
            "metadata": citation.metadata,
        }
        for citation in result.citations[:max_citations]
    ]


def _citation_from_row(row: dict[str, Any]) -> RagCitation:
    return RagCitation(
        document_id=str(row["document_id"]),
        chunk_id=str(row["chunk_id"]) if row.get("chunk_id") else None,
        title=str(row.get("title") or "Untitled reference"),
        source_type=row.get("source_type") or "career_guidance",
        source_url=row.get("source_url"),
        chunk_index=int(row.get("chunk_index") or 0),
        content=str(row.get("content") or ""),
        score=round(float(row.get("score") or 0), 4),
        metadata=row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
    )


def _lexical_score(query: str, content: str) -> float:
    query_terms = {term for term in query.lower().split() if len(term) > 2}
    content_terms = {term for term in content.lower().split() if len(term) > 2}
    if not query_terms:
        return 0.0
    return len(query_terms & content_terms) / len(query_terms)
