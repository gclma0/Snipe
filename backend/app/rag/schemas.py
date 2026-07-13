from typing import Any, Literal

from pydantic import BaseModel, Field

RagSourceType = Literal["job_description", "role_framework", "career_guidance", "job_listing"]


class RagChunk(BaseModel):
    chunk_index: int = Field(ge=0)
    content: str = Field(min_length=1)
    token_count: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)


class RagDocumentIngestion(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source_type: RagSourceType
    text: str = Field(min_length=100, max_length=100000)
    source_url: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagDocumentResult(BaseModel):
    document_id: str | None = None
    title: str
    source_type: RagSourceType
    content_hash: str
    chunk_count: int
    embedding_model: str


class RagDocumentSummary(BaseModel):
    document_id: str
    title: str
    source_type: RagSourceType
    source_url: str | None = None
    content_hash: str
    embedding_model: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class RagDocumentDeletionResult(BaseModel):
    document_id: str
    deleted: bool


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    source_types: list[RagSourceType] = Field(default_factory=list, max_length=4)
    limit: int = Field(default=5, ge=1, le=20)


class RagCitation(BaseModel):
    document_id: str
    chunk_id: str | None = None
    title: str
    source_type: RagSourceType
    source_url: str | None = None
    chunk_index: int
    content: str
    score: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagSearchResult(BaseModel):
    query: str
    embedding_model: str
    citations: list[RagCitation]
