"""Shared dataclasses and schemas for the RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_core.documents import Document


@dataclass(slots=True)
class ChunkMetadata:
    """Metadata attached to every retrieved chunk."""

    doc_id: str
    doc_name: str
    doc_type: str
    page: int | None
    section: str | None
    created_at: str
    chunk_index: int

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert metadata to a JSON-serializable dictionary."""

        return {
            "doc_id": self.doc_id,
            "doc_name": self.doc_name,
            "doc_type": self.doc_type,
            "page": self.page,
            "section": self.section,
            "created_at": self.created_at,
            "chunk_index": self.chunk_index,
        }


@dataclass(slots=True)
class Chunk:
    """Chunk passed through retrieval, reranking, and answer synthesis."""

    id: str
    text: str
    metadata: ChunkMetadata
    dense_score: float | None = None
    sparse_score: float | None = None
    fused_score: float | None = None
    rerank_score: float | None = None

    @classmethod
    def new(cls, text: str, metadata: ChunkMetadata) -> Chunk:
        """Create a new chunk with a generated UUID."""

        return cls(id=str(uuid4()), text=text, metadata=metadata)

    def to_debug_dict(self) -> dict[str, Any]:
        """Convert the chunk to a debug-friendly mapping."""

        return {
            "chunk_id": self.id,
            "text": self.text,
            "doc_name": self.metadata.doc_name,
            "doc_type": self.metadata.doc_type,
            "page": self.metadata.page,
            "section": self.metadata.section,
            "dense_score": self.dense_score,
            "sparse_score": self.sparse_score,
            "fused_score": self.fused_score,
            "rerank_score": self.rerank_score,
        }

    def to_langchain_document(self) -> Document:
        """Convert the chunk into a LangChain document."""

        return Document(
            page_content=self.text,
            metadata={
                **self.metadata.to_dict(),
                "chunk_id": self.id,
                "dense_score": self.dense_score,
                "sparse_score": self.sparse_score,
                "fused_score": self.fused_score,
                "rerank_score": self.rerank_score,
            },
        )


@dataclass(slots=True)
class ParsedBlock:
    """A normalized parsed block extracted from a source document."""

    text: str
    page: int | None = None
    section: str | None = None


@dataclass(slots=True)
class ParsedDocument:
    """A normalized parsed document before chunking."""

    doc_id: str
    doc_name: str
    doc_type: str
    blocks: list[ParsedBlock]
    created_at: str

    @classmethod
    def create(cls, doc_id: str, doc_name: str, doc_type: str, blocks: list[ParsedBlock]) -> ParsedDocument:
        """Create a parsed document with a timestamp."""

        return cls(
            doc_id=doc_id,
            doc_name=doc_name,
            doc_type=doc_type,
            blocks=blocks,
            created_at=datetime.now(UTC).isoformat(),
        )


@dataclass(slots=True)
class RetrievalResult:
    """Full retrieval bundle used by the pipeline and debug endpoint."""

    dense: list[Chunk]
    sparse: list[Chunk]
    fused: list[Chunk]
    retrieval_ms: int
