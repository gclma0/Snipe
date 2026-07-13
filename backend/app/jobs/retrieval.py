from typing import Any

from app.rag.retrieval import retrieve_rag_chunks
from app.rag.schemas import RagSearchRequest, RagSearchResult


def retrieve_job_references(
    *,
    query: str,
    user_id: str,
    supabase: Any,
    limit: int = 10,
) -> RagSearchResult:
    return retrieve_rag_chunks(
        RagSearchRequest(
            query=query,
            source_types=["job_description", "job_listing"],
            limit=limit,
        ),
        user_id=user_id,
        supabase=supabase,
    )
