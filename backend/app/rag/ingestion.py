import re
from hashlib import sha256
from typing import Any

from app.rag.embeddings import EMBEDDING_MODEL, embed_text
from app.rag.schemas import RagChunk, RagDocumentIngestion, RagDocumentResult

CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 35
MAX_CHUNKS_PER_DOCUMENT = 80
WORD_RE = re.compile(r"\S+")


def ingest_rag_document(
    document: RagDocumentIngestion,
    *,
    user_id: str,
    supabase: Any,
) -> RagDocumentResult:
    content_hash = rag_content_hash(document.text)
    chunks = chunk_text(document.text)
    row = supabase.create_rag_document(
        {
            "user_id": user_id,
            "title": document.title,
            "source_type": document.source_type,
            "source_url": document.source_url,
            "content_hash": content_hash,
            "metadata": document.metadata,
            "embedding_model": EMBEDDING_MODEL,
        }
    )
    document_id = row.get("id")
    payloads = build_rag_chunk_payloads(
        document_id=document_id,
        user_id=user_id,
        chunks=chunks,
    )
    supabase.create_rag_chunks(payloads)
    return RagDocumentResult(
        document_id=document_id,
        title=document.title,
        source_type=document.source_type,
        content_hash=content_hash,
        chunk_count=len(chunks),
        embedding_model=EMBEDDING_MODEL,
    )


def replace_rag_document(
    document_id: str,
    document: RagDocumentIngestion,
    *,
    user_id: str,
    supabase: Any,
) -> RagDocumentResult | None:
    content_hash = rag_content_hash(document.text)
    chunks = chunk_text(document.text)
    row = supabase.update_rag_document(
        user_id=user_id,
        document_id=document_id,
        payload={
            "title": document.title,
            "source_type": document.source_type,
            "source_url": document.source_url,
            "content_hash": content_hash,
            "metadata": document.metadata,
            "embedding_model": EMBEDDING_MODEL,
        },
    )
    if not row:
        return None

    supabase.delete_rag_chunks(user_id=user_id, document_id=document_id)
    supabase.create_rag_chunks(
        build_rag_chunk_payloads(
            document_id=document_id,
            user_id=user_id,
            chunks=chunks,
        )
    )
    return RagDocumentResult(
        document_id=document_id,
        title=document.title,
        source_type=document.source_type,
        content_hash=content_hash,
        chunk_count=len(chunks),
        embedding_model=EMBEDDING_MODEL,
    )


def build_rag_chunk_payloads(
    *,
    document_id: str | None,
    user_id: str,
    chunks: list[RagChunk],
) -> list[dict[str, Any]]:
    return [
        {
            "document_id": document_id,
            "user_id": user_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "token_count": chunk.token_count,
            "embedding": chunk.embedding,
            "metadata": chunk.metadata,
        }
        for chunk in chunks
        if document_id
    ]


def chunk_text(
    text: str,
    *,
    chunk_size_words: int = CHUNK_SIZE_WORDS,
    overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[RagChunk]:
    words = WORD_RE.findall(_normalize_text(text))
    if not words:
        return []
    if chunk_size_words <= overlap_words:
        raise ValueError("chunk_size_words must be greater than overlap_words.")

    chunks: list[RagChunk] = []
    start = 0
    while start < len(words) and len(chunks) < MAX_CHUNKS_PER_DOCUMENT:
        end = min(start + chunk_size_words, len(words))
        content = " ".join(words[start:end])
        chunks.append(
            RagChunk(
                chunk_index=len(chunks),
                content=content,
                token_count=end - start,
                metadata={"word_start": start, "word_end": end},
                embedding=embed_text(content),
            )
        )
        if end == len(words):
            break
        start = end - overlap_words
    return chunks


def rag_content_hash(text: str) -> str:
    return sha256(_normalize_text(text).encode("utf-8")).hexdigest()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
