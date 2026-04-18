"""Chunking strategies for different document types."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.rag.types import Chunk, ChunkMetadata, ParsedBlock, ParsedDocument


class DocumentChunker:
    """Split parsed documents into retrieval-friendly chunks."""

    policy_clause_pattern = re.compile(r"(第[一二三四五六七八九十百千]+条|[0-9]{1,2}[、.])")

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Chunk a parsed document according to its type."""

        if document.doc_type == "policy":
            return self._chunk_policy(document)
        if document.doc_type == "manual":
            return self._chunk_manual(document)
        if document.doc_type == "ticket":
            return self._chunk_ticket(document)
        return self._chunk_case(document)

    def _chunk_policy(self, document: ParsedDocument) -> list[Chunk]:
        """Split policy documents on legal clauses with overlap."""

        chunks: list[Chunk] = []
        for block in document.blocks:
            clauses = self._split_by_pattern(block.text, self.policy_clause_pattern)
            if not clauses:
                clauses = [block.text]
            for part in clauses:
                for piece in self._window_text(part, chunk_size=512, overlap=64):
                    chunks.append(self._build_chunk(document, piece, len(chunks), block))
        return chunks

    def _chunk_manual(self, document: ParsedDocument) -> list[Chunk]:
        """Chunk manuals while preserving heading context."""

        chunks: list[Chunk] = []
        buffer: list[str] = []
        current_section: str | None = None
        for block in document.blocks:
            if block.section != current_section and buffer:
                chunks.extend(
                    self._emit_buffer(document, "\n".join(buffer), current_section, len(chunks))
                )
                buffer = []
            current_section = block.section or current_section
            buffer.append(block.text)
        if buffer:
            chunks.extend(self._emit_buffer(document, "\n".join(buffer), current_section, len(chunks)))
        return chunks

    def _chunk_ticket(self, document: ParsedDocument) -> list[Chunk]:
        """Keep each structured record as a single chunk."""

        return [self._build_chunk(document, block.text, index, block) for index, block in enumerate(document.blocks)]

    def _chunk_case(self, document: ParsedDocument) -> list[Chunk]:
        """Chunk typical cases in larger paragraph-level windows."""

        content = "\n".join(block.text for block in document.blocks if block.text.strip())
        chunks: list[Chunk] = []
        for index, part in enumerate(self._window_text(content, chunk_size=1024, overlap=96)):
            block = ParsedBlock(text=part)
            chunks.append(self._build_chunk(document, part, index, block))
        return chunks

    def _emit_buffer(
        self,
        document: ParsedDocument,
        content: str,
        section: str | None,
        start_index: int,
    ) -> list[Chunk]:
        """Emit manual chunks from a content buffer."""

        block = ParsedBlock(text=content, section=section)
        return [
            self._build_chunk(document, part, start_index + offset, block)
            for offset, part in enumerate(self._window_text(content, chunk_size=512, overlap=64))
        ]

    def _split_by_pattern(self, text: str, pattern: re.Pattern[str]) -> list[str]:
        """Split text while retaining semantic clause markers."""

        matches = list(pattern.finditer(text))
        if not matches:
            return [text.strip()] if text.strip() else []

        parts: list[str] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            part = text[start:end].strip()
            if part:
                parts.append(part)
        return parts

    def _window_text(self, text: str, chunk_size: int, overlap: int) -> Iterable[str]:
        """Create overlapping windows over the text using character counts."""

        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return []
        if len(cleaned) <= chunk_size:
            return [cleaned]

        parts: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(start + chunk_size, len(cleaned))
            parts.append(cleaned[start:end])
            if end >= len(cleaned):
                break
            start = max(end - overlap, start + 1)
        return parts

    def _build_chunk(
        self,
        document: ParsedDocument,
        text: str,
        index: int,
        block: ParsedBlock,
    ) -> Chunk:
        """Build a chunk instance with the required metadata."""

        metadata = ChunkMetadata(
            doc_id=document.doc_id,
            doc_name=document.doc_name,
            doc_type=document.doc_type,
            page=block.page,
            section=block.section,
            created_at=document.created_at,
            chunk_index=index,
        )
        return Chunk.new(text=text, metadata=metadata)

