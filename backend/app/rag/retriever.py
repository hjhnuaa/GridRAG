"""Hybrid retriever using Chroma and BM25."""

from __future__ import annotations

import importlib
import time
import warnings
from collections import defaultdict
from functools import lru_cache
from typing import Any, Protocol, cast

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.ingest.embedder import EmbeddingService, get_embedding_service
from app.models.document import DocumentChunk
from app.models.enums import DocType
from app.rag.store import ChromaStore, get_chroma_store
from app.rag.types import Chunk, ChunkMetadata, RetrievalResult


class _JiebaModule(Protocol):
    """Protocol for the subset of jieba used by the retriever."""

    def lcut_for_search(self, text: str) -> list[str]:
        """Tokenize text for search."""


class _BM25Model(Protocol):
    """Protocol for the BM25 scorer instance."""

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        """Return BM25 scores for the query tokens."""


class _BM25Factory(Protocol):
    """Protocol for the BM25 constructor."""

    def __call__(self, corpus: list[list[str]]) -> _BM25Model:
        """Construct a BM25 scorer from tokenized documents."""


@lru_cache(maxsize=1)
def _get_jieba_module() -> _JiebaModule:
    """Import jieba lazily to avoid eager import warnings at startup."""

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pkg_resources is deprecated as an API.*",
            category=UserWarning,
        )
        return cast(_JiebaModule, importlib.import_module("jieba"))


@lru_cache(maxsize=1)
def _get_bm25_class() -> _BM25Factory:
    """Import the BM25 implementation lazily."""

    module = importlib.import_module("rank_bm25")
    return cast(_BM25Factory, cast(Any, module).BM25Okapi)


class HybridRetriever:
    """Combine dense retrieval and BM25 sparse retrieval via RRF."""

    def __init__(
        self,
        embedder: EmbeddingService | None = None,
        chroma_store: ChromaStore | None = None,
    ) -> None:
        """Initialize retriever dependencies."""

        self.settings = get_settings()
        self.embedder = embedder or get_embedding_service()
        self.chroma_store = chroma_store or get_chroma_store()

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        doc_types: list[str] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """Run dense and sparse retrieval and fuse the results."""

        started_at = time.perf_counter()
        target_k = top_k or self.settings.rag_retrieval_top_k
        embedding = await self.embedder.embed_query(query)
        dense = await self._vector_search(embedding, doc_types=doc_types, k=target_k)
        sparse = await self._bm25_search(session, query, doc_types=doc_types, k=target_k)
        fused = self._rrf_merge(dense, sparse, k=60)[:target_k]
        retrieval_ms = int((time.perf_counter() - started_at) * 1000)
        return RetrievalResult(dense=dense, sparse=sparse, fused=fused, retrieval_ms=retrieval_ms)

    async def _vector_search(
        self,
        embedding: list[float],
        doc_types: list[str] | None,
        k: int,
    ) -> list[Chunk]:
        """Retrieve chunks from Chroma collections."""

        target_doc_types = doc_types or [item.value for item in DocType]
        candidates: dict[str, Chunk] = {}
        for doc_type in target_doc_types:
            results = self.chroma_store.query(doc_type=doc_type, embedding=embedding, top_k=k)
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances, strict=False):
                similarity = max(0.0, 1.0 - float(distance or 0))
                chunk = Chunk(
                    id=str(chunk_id),
                    text=str(text),
                    metadata=ChunkMetadata(
                        doc_id=str(metadata.get("doc_id")),
                        doc_name=str(metadata.get("doc_name")),
                        doc_type=str(metadata.get("doc_type")),
                        page=int(metadata["page"]) if metadata.get("page") is not None else None,
                        section=str(metadata["section"]) if metadata.get("section") else None,
                        created_at=str(metadata.get("created_at")),
                        chunk_index=int(metadata.get("chunk_index", 0)),
                    ),
                    dense_score=similarity,
                )
                if chunk.id not in candidates or (candidates[chunk.id].dense_score or 0) < similarity:
                    candidates[chunk.id] = chunk
        return sorted(candidates.values(), key=lambda item: item.dense_score or 0, reverse=True)[:k]

    async def _bm25_search(
        self,
        session: AsyncSession,
        query: str,
        doc_types: list[str] | None,
        k: int,
    ) -> list[Chunk]:
        """Retrieve chunks using BM25 over stored text chunks."""

        stmt: Select[tuple[DocumentChunk]] = select(DocumentChunk)
        if doc_types:
            stmt = stmt.where(DocumentChunk.doc_type.in_(doc_types))
        rows = (await session.execute(stmt)).scalars().all()
        if not rows:
            return []

        tokenized_docs = [self._tokenize(row.text) for row in rows]
        bm25_class = _get_bm25_class()
        bm25 = bm25_class(tokenized_docs)
        query_tokens = self._tokenize(query)
        scores = bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(rows, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )[:k]
        top_score = float(ranked[0][1]) if ranked else 0.0

        candidates: list[Chunk] = []
        for row, raw_score in ranked:
            normalized = 0.0 if top_score <= 0 else max(0.0, float(raw_score) / top_score)
            candidates.append(
                Chunk(
                    id=row.id,
                    text=row.text,
                    metadata=ChunkMetadata(
                        doc_id=row.document_id,
                        doc_name=row.doc_name,
                        doc_type=row.doc_type,
                        page=row.page,
                        section=row.section,
                        created_at=row.created_at.isoformat(),
                        chunk_index=row.chunk_index,
                    ),
                    sparse_score=normalized,
                )
            )
        return candidates

    def _rrf_merge(self, dense: list[Chunk], sparse: list[Chunk], k: int = 60) -> list[Chunk]:
        """Fuse two ranking lists with reciprocal rank fusion."""

        merged: dict[str, Chunk] = {}
        scores: defaultdict[str, float] = defaultdict(float)

        # RRF 只关心候选在各路召回中的名次，能降低不同评分尺度带来的偏差。
        for rank, chunk in enumerate(dense, start=1):
            merged.setdefault(chunk.id, chunk)
            scores[chunk.id] += 1 / (k + rank)

        for rank, chunk in enumerate(sparse, start=1):
            if chunk.id in merged:
                merged_chunk = merged[chunk.id]
                merged_chunk.sparse_score = chunk.sparse_score
            else:
                merged[chunk.id] = chunk
            scores[chunk.id] += 1 / (k + rank)

        fused = list(merged.values())
        for item in fused:
            item.fused_score = scores[item.id]
        return sorted(fused, key=lambda item: item.fused_score or 0, reverse=True)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize Chinese text for BM25."""

        jieba_module = _get_jieba_module()
        return [token.strip() for token in jieba_module.lcut_for_search(text) if token.strip()]

    def as_langchain_retriever(
        self,
        session: AsyncSession,
        doc_types: list[str] | None = None,
        top_k: int | None = None,
    ) -> LangChainHybridRetriever:
        """Wrap the retriever as a LangChain BaseRetriever."""

        return LangChainHybridRetriever(
            retriever=self,
            session=session,
            doc_types=doc_types,
            top_k=top_k,
        )


class LangChainHybridRetriever(BaseRetriever):
    """LangChain-compatible adapter over the existing hybrid retriever."""

    retriever: HybridRetriever
    session: AsyncSession
    doc_types: list[str] | None = None
    top_k: int | None = None

    class Config:
        """Allow arbitrary runtime dependencies in the retriever wrapper."""

        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str, *, run_manager: Any = None) -> list[Document]:
        """Synchronous retrieval is not supported for this adapter."""

        raise NotImplementedError("Use ainvoke/aget_relevant_documents with AsyncSession-backed retrieval.")

    async def _aget_relevant_documents(self, query: str, *, run_manager: Any = None) -> list[Document]:
        """Return fused retrieval results as LangChain documents."""

        result = await self.retriever.retrieve(
            self.session,
            query,
            doc_types=self.doc_types,
            top_k=self.top_k,
        )
        return [chunk.to_langchain_document() for chunk in result.fused]
