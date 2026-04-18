"""Tests for document chunking behavior."""

from __future__ import annotations

from app.rag.chunker import DocumentChunker
from app.rag.types import ParsedBlock, ParsedDocument


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

