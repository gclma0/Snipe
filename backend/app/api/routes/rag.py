from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.jobs.retrieval import retrieve_job_references
from app.rag.ingestion import ingest_rag_document
from app.rag.retrieval import retrieve_rag_chunks
from app.rag.schemas import (
    RagDocumentIngestion,
    RagDocumentResult,
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
