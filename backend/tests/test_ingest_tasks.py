"""Tests for asynchronous document ingestion guards."""

from __future__ import annotations

from app.ingest.tasks import EMPTY_DOCUMENT_ERROR
from app.rag.chunker import DocumentChunker
from app.rag.types import ParsedDocument


def test_empty_document_chunks_are_rejected_before_embedding() -> None:
    """Empty parsed documents should not continue into embedding or vector indexing."""

    document = ParsedDocument.create(
        doc_id="doc-empty",
        doc_name="空文档",
        doc_type="policy",
        blocks=[],
    )

    assert DocumentChunker().chunk(document) == []
    assert EMPTY_DOCUMENT_ERROR == "文档未解析到可入库文本，请检查文件内容或格式。"
