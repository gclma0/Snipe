from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.jobs.retrieval import retrieve_job_references
from app.rag.ingestion import ingest_rag_document
from app.rag.retrieval import retrieve_rag_chunks
from app.rag.schemas import (
    RagDocumentDeletionResult,
    RagDocumentIngestion,
    RagDocumentResult,
    RagDocumentSummary,
    RagSearchRequest,
    RagSearchResult,
)
from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/rag", tags=["rag"])
CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)


@router.post("/documents", response_model=RagDocumentResult, status_code=status.HTTP_201_CREATED)
def create_rag_document(
    payload: RagDocumentIngestion,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> RagDocumentResult:
    try:
        return ingest_rag_document(payload, user_id=user.id, supabase=supabase)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.get("/documents", response_model=list[RagDocumentSummary])
def list_rag_documents(
    limit: int = 20,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> list[RagDocumentSummary]:
    try:
        rows = supabase.list_rag_documents(
            user_id=user.id,
            limit=max(1, min(limit, 50)),
        )
        return [
            RagDocumentSummary(
                document_id=row["id"],
                title=row["title"],
                source_type=row["source_type"],
                source_url=row.get("source_url"),
                content_hash=row["content_hash"],
                embedding_model=row["embedding_model"],
                metadata=row.get("metadata") or {},
                created_at=row.get("created_at"),
            )
            for row in rows
        ]
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.delete("/documents/{document_id}", response_model=RagDocumentDeletionResult)
def delete_rag_document(
    document_id: str,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> RagDocumentDeletionResult:
    try:
        deleted = supabase.delete_rag_document(user_id=user.id, document_id=document_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RAG document not found.",
            )
        return RagDocumentDeletionResult(document_id=document_id, deleted=True)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.post("/search", response_model=RagSearchResult)
def search_rag_documents(
    payload: RagSearchRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> RagSearchResult:
    try:
        return retrieve_rag_chunks(payload, user_id=user.id, supabase=supabase)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc


@router.post("/jobs/search", response_model=RagSearchResult)
def search_job_references(
    payload: RagSearchRequest,
    user: AuthenticatedUser = CurrentUser,
    supabase: SupabaseClient = Supabase,
) -> RagSearchResult:
    try:
        return retrieve_job_references(
            query=payload.query,
            user_id=user.id,
            supabase=supabase,
            limit=payload.limit,
        )
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase operation failed.",
        ) from exc
