"""Persistent Chroma vector store helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

import chromadb

from app.core.config import get_settings
from app.models.enums import DocType
from app.rag.types import Chunk


class ChromaStore:
    """Thin wrapper around Chroma persistent collections."""

    def __init__(self) -> None:
        """Initialize the Chroma client."""

        settings = get_settings()
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))

    def collection_name(self, doc_type: str) -> str:
        """Build the collection name from the document type."""

        return f"{self.settings.chroma_collection_prefix}_{doc_type}"

    def get_collection(self, doc_type: str) -> Any:
        """Return an existing collection or create it if needed."""

        return self.client.get_or_create_collection(
            name=self.collection_name(doc_type),
            metadata={"hnsw:space": "cosine"},
        )

    def all_doc_types(self) -> list[str]:
        """Return all known collection types."""

        return [item.value for item in DocType]

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Upsert chunks and embeddings into Chroma collections."""

        grouped: dict[str, dict[str, list[Any]]] = {}
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            group = grouped.setdefault(
                chunk.metadata.doc_type,
                {"ids": [], "documents": [], "metadatas": [], "embeddings": []},
            )
            group["ids"].append(chunk.id)
            group["documents"].append(chunk.text)
            group["metadatas"].append(chunk.metadata.to_dict())
            group["embeddings"].append(embedding)

        for doc_type, payload in grouped.items():
            collection = self.get_collection(doc_type)
            collection.upsert(
                ids=payload["ids"],
                documents=payload["documents"],
                metadatas=payload["metadatas"],
                embeddings=payload["embeddings"],
            )

    def delete_document(self, document_id: str, doc_type: str | None = None) -> None:
        """Delete all chunks for a document."""

        target_types = [doc_type] if doc_type else self.all_doc_types()
        for target_type in target_types:
            collection = self.get_collection(target_type)
            collection.delete(where={"doc_id": document_id})

    def query(self, doc_type: str, embedding: list[float], top_k: int) -> dict[str, list[list[Any]]]:
        """Query a single collection."""

        collection = self.get_collection(doc_type)
        return cast(
            dict[str, list[list[Any]]],
            collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            ),
        )


@lru_cache(maxsize=1)
def get_chroma_store() -> ChromaStore:
    """Return a cached Chroma store instance."""

    return ChromaStore()
