"""Schemas for chat and RAG debug APIs."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseSchema


class ChatFilters(BaseSchema):
    """Optional filters for RAG retrieval."""

    doc_types: list[str] = Field(default_factory=list)


class ChatAskRequest(BaseSchema):
    """Incoming question for the chat endpoint."""

    session_id: str
    question: str = Field(min_length=1, max_length=2000)
    filters: ChatFilters = Field(default_factory=ChatFilters)


class SourceItem(BaseSchema):
    """Citation returned with a grounded answer."""

    chunk_id: str | None = None
    doc_id: str | None = None
    doc_name: str
    doc_type: str
    page: int | None = None
    section: str | None = None
    excerpt: str
    score: float | None = None


class ChatMessage(BaseSchema):
    """A single chat message."""

    id: str
    session_id: str
    role: str
    content: str
    sources: list[SourceItem] | None = None
    created_at: str


class RetrievalCandidate(BaseSchema):
    """A retrieval candidate for debug purposes."""

    chunk_id: str
    text: str
    doc_name: str
    doc_type: str
    page: int | None = None
    section: str | None = None
    dense_score: float | None = None
    sparse_score: float | None = None
    fused_score: float | None = None
    rerank_score: float | None = None


class ChatDebugResponse(BaseSchema):
    """Detailed RAG pipeline debug payload."""

    original_query: str
    rewritten_query: str
    grounded: bool
    prompt_preview: str
    dense_candidates: list[RetrievalCandidate]
    sparse_candidates: list[RetrievalCandidate]
    fused_candidates: list[RetrievalCandidate]
    reranked_candidates: list[RetrievalCandidate]
    selected_sources: list[SourceItem]

