"""Schemas for knowledge document APIs."""

from __future__ import annotations

from datetime import datetime

from app.models.enums import DocType, IngestStatus
from app.schemas.common import BaseSchema


class DocumentResponse(BaseSchema):
    """Knowledge document payload."""

    id: str
    name: str
    doc_type: DocType
    file_path: str
    file_size: int
    status: IngestStatus
    chunk_count: int
    error_msg: str | None = None
    uploaded_by: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None


class KnowledgeStatsResponse(BaseSchema):
    """Aggregated statistics for the knowledge base."""

    total_documents: int
    total_chunks: int
    by_type: list[dict[str, int | str]]
    processing_documents: int

