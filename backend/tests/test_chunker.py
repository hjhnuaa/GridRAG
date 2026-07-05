"""Tests for document chunking behavior."""

from __future__ import annotations

from app.rag.chunker import DocumentChunker
from app.rag.sources import (
    build_chunk_sources,
    build_web_sources,
    filter_chunk_sources_by_citation,
    filter_web_sources_by_citation,
)
from app.rag.types import Chunk, ChunkMetadata, ParsedBlock, ParsedDocument
from app.schemas.web_search import WebSearchResult


def test_policy_chunker_preserves_metadata() -> None:
    """Policy chunking should preserve required metadata."""

    chunker = DocumentChunker()
    document = ParsedDocument.create(
        doc_id="doc-1",
        doc_name="低保政策",
        doc_type="policy",
        blocks=[
            ParsedBlock(text="第一条 申请人需提交身份证明。第二条 申请人需提交家庭收入说明。", page=1),
        ],
    )

    chunks = chunker.chunk(document)

    assert chunks
    assert chunks[0].metadata.doc_id == "doc-1"
    assert chunks[0].metadata.doc_name == "低保政策"
    assert chunks[0].metadata.page == 1


def _chunk(chunk_id: str, text: str, score: float) -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            doc_id="doc-1",
            doc_name="低保政策",
            doc_type="policy",
            page=1,
            section="申请材料",
            created_at="2026-01-01T00:00:00+00:00",
            chunk_index=1,
        ),
        rerank_score=score,
    )


def test_filter_chunk_sources_by_citation_uses_answer_indexes() -> None:
    """Local citation markers should map back to the same ordered chunks used in the prompt."""

    chunks = [
        _chunk("chunk-1", "第一段：申请对象。", 0.8),
        _chunk("chunk-2", "第二段：申请材料。", 0.7),
    ]
    fallback = build_chunk_sources(chunks)

    selected = filter_chunk_sources_by_citation("请优先准备身份证和收入证明。[2]", chunks, fallback)

    assert [item.chunk_id for item in selected] == ["chunk-2"]
    assert selected[0].excerpt == "第二段：申请材料。"


def test_filter_chunk_sources_by_citation_falls_back_without_markers() -> None:
    """Answers without citation markers should still expose selected local context."""

    chunks = [_chunk("chunk-1", "第一段：申请对象。", 0.8)]
    fallback = build_chunk_sources(chunks)

    selected = filter_chunk_sources_by_citation("未写引用标记的回答", chunks, fallback)

    assert selected == fallback


def test_filter_web_sources_by_citation_supports_w_markers() -> None:
    """Web citation markers should map to normalized web search sources."""

    results = [
        WebSearchResult(title="网页一", url="https://example.com/1", snippet="摘要一", provider="serper", score=0.9),
        WebSearchResult(title="网页二", url="https://example.com/2", snippet="摘要二", provider="serper", score=0.8),
    ]

    selected = filter_web_sources_by_citation("可参考最新网页。[W2]", results)

    assert [item.doc_name for item in selected] == ["网页二"]
    assert selected[0].url == "https://example.com/2"


def test_build_web_sources_returns_all_results_without_markers() -> None:
    """When the answer omits web markers, all web search results remain visible as context."""

    results = [
        WebSearchResult(title="网页一", url="https://example.com/1", snippet="", provider="serper", score=None),
    ]

    assert filter_web_sources_by_citation("未写联网引用标记", results) == build_web_sources(results)
