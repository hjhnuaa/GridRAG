"""Normalize loaded files into parsed documents."""

from __future__ import annotations

from pathlib import Path

from app.ingest.loader import DocumentLoader
from app.rag.types import ParsedDocument


class DocumentParser:
    """Convert source files into normalized parsed documents."""

    def __init__(self, loader: DocumentLoader | None = None) -> None:
        """Initialize the parser."""

        self.loader = loader or DocumentLoader()

    def parse(self, document_id: str, file_path: Path, doc_name: str, doc_type: str) -> ParsedDocument:
        """Parse a source file into blocks."""

        blocks = self.loader.load(file_path)
        return ParsedDocument.create(
            doc_id=document_id,
            doc_name=doc_name,
            doc_type=doc_type,
            blocks=blocks,
        )

