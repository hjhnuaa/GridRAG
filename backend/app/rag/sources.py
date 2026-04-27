"""RAG answer source helpers."""

from __future__ import annotations

import re

from app.rag.types import Chunk
from app.schemas.chat import SourceItem
from app.schemas.web_search import WebSearchResult


def build_chunk_sources(chunks: list[Chunk]) -> list[SourceItem]:
    """Convert selected local chunks into response source items."""

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


def build_web_sources(web_results: list[WebSearchResult]) -> list[SourceItem]:
    """Convert normalized web search results into response source items."""

    return [
        SourceItem(
            chunk_id=None,
            doc_id=None,
            doc_name=result.title,
            doc_type=f"web:{result.provider}",
            page=None,
            section=None,
            excerpt=result.snippet or result.url,
            score=result.score,
            url=result.url,
        )
        for result in web_results
    ]


def filter_chunk_sources_by_citation(
    answer_text: str,
    chunks: list[Chunk],
    fallback: list[SourceItem],
) -> list[SourceItem]:
    """Map citation markers like [1] back to retrieved local chunks."""

    indexes = {int(value) for value in re.findall(r"\[(\d+)\]", answer_text)}
    if not indexes:
        return fallback

    mapped: list[SourceItem] = []
    for index in sorted(indexes):
        if 1 <= index <= len(chunks):
            # Prompt 中的本地引用从 1 开始，列表下标从 0 开始，这里统一做一次转换。
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


def filter_web_sources_by_citation(answer_text: str, web_results: list[WebSearchResult]) -> list[SourceItem]:
    """Map web citation markers like [W1] back to web search results."""

    web_sources = build_web_sources(web_results)
    if not web_sources:
        return []

    indexes = {int(value) for value in re.findall(r"\[W(\d+)\]", answer_text, flags=re.IGNORECASE)}
    if not indexes:
        return web_sources
    return [web_sources[index - 1] for index in sorted(indexes) if 1 <= index <= len(web_sources)]
