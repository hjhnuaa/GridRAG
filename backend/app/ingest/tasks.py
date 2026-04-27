"""Celery tasks for asynchronous document ingest."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from celery import Celery

from app.core.config import get_settings
from app.core.database import AsyncSessionFactory
from app.core.logging import get_logger
from app.ingest.embedder import get_embedding_service
from app.ingest.loader import DocumentParser
from app.models.document import DocumentChunk
from app.rag.chunker import DocumentChunker
from app.rag.store import get_chroma_store
from app.services.documents import (
    get_document_or_404,
    mark_document_done,
    mark_document_failed,
    mark_document_processing,
    replace_document_chunks,
)

logger = get_logger(__name__)
settings = get_settings()

celery_app = Celery("gridrag", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.task_always_eager = settings.celery_task_always_eager


async def ingest_document(document_id: str) -> None:
    """Parse, chunk, embed, and index a document."""

    parser = DocumentParser()
    chunker = DocumentChunker()
    embedder = get_embedding_service()
    store = get_chroma_store()

    async with AsyncSessionFactory() as session:
        await mark_document_processing(session, document_id)
        document = await get_document_or_404(session, document_id)
        try:
            parsed_document = parser.parse(
                document_id=document.id,
                file_path=Path(document.file_path),
                doc_name=document.name,
                doc_type=str(document.doc_type),
            )
            chunks = chunker.chunk(parsed_document)
            embeddings = await embedder.embed_texts([chunk.text for chunk in chunks])
            orm_chunks = [
                DocumentChunk(
                    id=chunk.id,
                    document_id=document.id,
                    doc_name=chunk.metadata.doc_name,
                    doc_type=chunk.metadata.doc_type,
                    text=chunk.text,
                    page=chunk.metadata.page,
                    section=chunk.metadata.section,
                    chunk_index=chunk.metadata.chunk_index,
                    metadata_json=chunk.metadata.to_dict(),
                    embedding_model=settings.embedding_model,
                    created_at=datetime.now(UTC),
                )
                for chunk in chunks
            ]
            await replace_document_chunks(session, document.id, orm_chunks)
            store.delete_document(document.id, str(document.doc_type))
            store.upsert_chunks(chunks, embeddings)
            await mark_document_done(session, document.id, chunk_count=len(chunks))
        except Exception as exc:
            logger.exception("document_ingest_failed", document_id=document_id, error=str(exc))
            await mark_document_failed(session, document_id, str(exc))
            raise


@celery_app.task(name="app.ingest.tasks.process_document")  # type: ignore[untyped-decorator]
def process_document_task(document_id: str) -> None:
    """Celery task entrypoint."""

    asyncio.run(ingest_document(document_id))


def trigger_document_ingestion(document_id: str) -> None:
    """Enqueue or execute a document ingest task."""

    process_document_task.delay(document_id)
