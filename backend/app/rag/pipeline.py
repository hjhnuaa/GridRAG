"""End-to-end RAG pipeline with streaming answers and debug output."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache, get_cache
from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.generator import QwenGenerator, get_qwen_generator
from app.rag.reranker import BGEReranker, get_reranker
from app.rag.retriever import HybridRetriever
from app.rag.types import Chunk
from app.schemas.chat import ChatDebugResponse, RetrievalCandidate, SourceItem
from app.services import chat as chat_service

logger = get_logger(__name__)


class RAGPipeline:
    """Coordinate retrieval, reranking, prompting, streaming, and persistence."""

    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        reranker: BGEReranker | None = None,
        generator: QwenGenerator | None = None,
        cache: RedisCache | None = None,
    ) -> None:
        """Initialize the pipeline."""

        self.settings = get_settings()
        self.retriever = retriever or HybridRetriever()
        self.reranker = reranker or get_reranker()
        self.generator = generator or get_qwen_generator()
        self.cache = cache or get_cache()

    async def stream_answer(
        self,
        session: AsyncSession,
        session_id: str,
        question: str,
        doc_types: list[str] | None = None,
    ) -> AsyncGenerator[dict[str, object], None]:
        """Stream an answer as SSE-ready dictionaries."""

        normalized_query = self.rewrite_query(question)
        cache_key = self._cache_key(normalized_query, doc_types)
        cached = await self.cache.get_json(cache_key)
        if isinstance(cached, dict):
            logger.info("rag_cache_hit", cache_key=cache_key)
            cached_answer = str(cached.get("answer", ""))
            cached_sources = cached.get("sources", [])
            yield {"type": "chunk", "content": cached_answer}
            yield {"type": "sources", "sources": cached_sources}
            yield {"type": "done"}
            await chat_service.save_chat_message(session, session_id, "assistant", cached_answer, cached_sources)
            return

        retrieval = await self.retriever.retrieve(session, normalized_query, doc_types=doc_types)
        reranked = await self.reranker.rerank(normalized_query, retrieval.fused)
        grounded = any((item.rerank_score or 0) >= self.settings.rag_min_relevance_score for item in reranked)
        prompt_preview = ""
        answer_parts: list[str] = []
        sources: list[SourceItem] = []
        try:
            if not grounded:
                fallback = "未在知识库中找到相关信息，建议联系上级部门或查阅原始政策文件。"
                yield {"type": "chunk", "content": fallback}
                yield {"type": "sources", "sources": []}
                yield {"type": "done"}
                await chat_service.save_chat_message(session, session_id, "assistant", fallback, [])
            else:
                selected_chunks = self._trim_context_chunks(reranked)
                sources = self._build_sources(selected_chunks)
                prompt_preview = self.generator.render_prompt(
                    "qa_system.j2",
                    contexts=selected_chunks,
                    question=question,
                )
                stream = await self.generator.stream_completion(prompt_preview)
                async for part in stream:
                    delta = part.choices[0].delta.content or ""
                    if not delta:
                        continue
                    answer_parts.append(delta)
                    yield {"type": "chunk", "content": delta}
                answer_text = "".join(answer_parts).strip()
                cited_sources = self._filter_sources_by_citation(answer_text, selected_chunks, fallback=sources)
                serialized_sources = [item.model_dump() for item in cited_sources]
                yield {"type": "sources", "sources": serialized_sources}
                yield {"type": "done"}
                await chat_service.save_chat_message(session, session_id, "assistant", answer_text, serialized_sources)
                await self.cache.set_json(
                    cache_key,
                    {"answer": answer_text, "sources": serialized_sources},
                    ttl=self.settings.cache_ttl_seconds,
                )
        finally:
            await chat_service.save_retrieval_log(
                session=session,
                session_id=session_id,
                query=question,
                rewritten_query=normalized_query,
                filters={"doc_types": doc_types or []},
                retrieval_ms=retrieval.retrieval_ms,
                rerank_scores=[
                    {"chunk_id": item.id, "score": item.rerank_score or 0.0, "doc_name": item.metadata.doc_name}
                    for item in reranked
                ],
                top_chunks=[item.to_debug_dict() for item in reranked],
                is_grounded=grounded,
            )

    async def debug(
        self,
        session: AsyncSession,
        question: str,
        doc_types: list[str] | None = None,
    ) -> ChatDebugResponse:
        """Return a non-streaming debug payload of the RAG execution."""

        rewritten_query = self.rewrite_query(question)
        retrieval = await self.retriever.retrieve(session, rewritten_query, doc_types=doc_types)
        reranked = await self.reranker.rerank(rewritten_query, retrieval.fused)
        grounded = any((item.rerank_score or 0) >= self.settings.rag_min_relevance_score for item in reranked)
        selected_chunks = self._trim_context_chunks(reranked)
        prompt_preview = self.generator.render_prompt(
            "qa_system.j2",
            contexts=selected_chunks,
            question=question,
        )
        sources = self._build_sources(selected_chunks)
        return ChatDebugResponse(
            original_query=question,
            rewritten_query=rewritten_query,
            grounded=grounded,
            prompt_preview=prompt_preview,
            dense_candidates=[RetrievalCandidate(**item.to_debug_dict()) for item in retrieval.dense],
            sparse_candidates=[RetrievalCandidate(**item.to_debug_dict()) for item in retrieval.sparse],
            fused_candidates=[RetrievalCandidate(**item.to_debug_dict()) for item in retrieval.fused],
            reranked_candidates=[RetrievalCandidate(**item.to_debug_dict()) for item in reranked],
            selected_sources=sources,
        )

    def rewrite_query(self, question: str) -> str:
        """Normalize the query for retrieval."""

        normalized = re.sub(r"\s+", " ", question).strip()
        return normalized

    def _trim_context_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Limit the number of context chunks by an estimated token budget."""

        budget = max(512, self.settings.rag_max_total_tokens - self.settings.qwen_max_tokens)
        total = 0
        selected: list[Chunk] = []
        for chunk in chunks:
            estimate = self._estimate_tokens(chunk.text)
            if selected and total + estimate > budget:
                break
            selected.append(chunk)
            total += estimate
        return selected[: self.settings.rag_rerank_top_n]

    def _build_sources(self, chunks: list[Chunk]) -> list[SourceItem]:
        """Convert selected chunks into source items."""

        return [
            SourceItem(
                chunk_id=chunk.id,
                doc_id=chunk.metadata.doc_id,
                doc_name=chunk.metadata.doc_name,
                doc_type=chunk.metadata.doc_type,
                page=chunk.metadata.page,
                section=chunk.metadata.section,
                excerpt=chunk.text[:220],
                score=chunk.rerank_score or chunk.fused_score or chunk.dense_score or chunk.sparse_score,
            )
            for chunk in chunks
        ]

    def _filter_sources_by_citation(
        self,
        answer_text: str,
        chunks: list[Chunk],
        fallback: list[SourceItem],
    ) -> list[SourceItem]:
        """Map citation markers like [1] back to retrieved sources."""

        indexes = {int(value) for value in re.findall(r"\[(\d+)\]", answer_text)}
        if not indexes:
            return fallback
        mapped: list[SourceItem] = []
        for index in sorted(indexes):
            if 1 <= index <= len(chunks):
                chunk = chunks[index - 1]
                mapped.append(
                    SourceItem(
                        chunk_id=chunk.id,
                        doc_id=chunk.metadata.doc_id,
                        doc_name=chunk.metadata.doc_name,
                        doc_type=chunk.metadata.doc_type,
                        page=chunk.metadata.page,
                        section=chunk.metadata.section,
                        excerpt=chunk.text[:220],
                        score=chunk.rerank_score,
                    )
                )
        return mapped or fallback

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token usage from string length."""

        return max(1, len(text) // 2)

    def _cache_key(self, question: str, doc_types: list[str] | None) -> str:
        """Generate a stable cache key."""

        payload = json.dumps({"question": question, "doc_types": sorted(doc_types or [])}, ensure_ascii=False)
        digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
        return f"rag:answer:{digest}"
