"""Service functions for knowledge document management."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.core.exceptions import AppError
from app.models.document import Document, DocumentChunk
from app.models.enums import DocType, IngestStatus
from app.schemas.common import PaginatedData, PaginationMeta
from app.schemas.document import DocumentResponse, KnowledgeStatsResponse


async def create_document_record(
    session: AsyncSession,
    name: str,
    doc_type: DocType,
    file_path: str,
    file_size: int,
    uploaded_by: str,
) -> Document:
    """Persist a newly uploaded document."""

    document = Document(
        name=name,
        doc_type=doc_type,
        file_path=file_path,
        file_size=file_size,
        status=IngestStatus.PENDING,
        uploaded_by=uploaded_by,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    await invalidate_knowledge_related_cache()
    return document


async def get_document_or_404(session: AsyncSession, document_id: str) -> Document:
    """Return a document or raise 404."""

    document = await session.get(Document, document_id)
    if document is None:
        raise AppError("未找到指定文档。", code=4043, status_code=status.HTTP_404_NOT_FOUND)
    return document


async def list_documents(
    session: AsyncSession,
    page: int,
    page_size: int,
    doc_type: str | None = None,
) -> PaginatedData[DocumentResponse]:
    """List knowledge documents."""

    stmt = select(Document).order_by(Document.created_at.desc())
    count_stmt = select(func.count()).select_from(Document)
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)
        count_stmt = count_stmt.where(Document.doc_type == doc_type)

    total = int((await session.execute(count_stmt)).scalar_one())
    docs = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedData(
        items=[DocumentResponse.model_validate(item) for item in docs],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


async def mark_document_processing(session: AsyncSession, document_id: str) -> Document:
    """Mark a document as being processed."""

    document = await get_document_or_404(session, document_id)
    document.status = IngestStatus.PROCESSING
    document.error_msg = None
    await session.commit()
    await session.refresh(document)
    await invalidate_knowledge_related_cache()
    return document


async def mark_document_done(session: AsyncSession, document_id: str, chunk_count: int) -> Document:
    """Mark a document as successfully indexed."""

    document = await get_document_or_404(session, document_id)
    document.status = IngestStatus.DONE
    document.chunk_count = chunk_count
    document.processed_at = datetime.now(UTC)
    document.error_msg = None
    await session.commit()
    await session.refresh(document)
    await invalidate_knowledge_related_cache()
    return document


async def mark_document_failed(session: AsyncSession, document_id: str, error_message: str) -> Document:
    """Mark a document as failed during ingest."""

    document = await get_document_or_404(session, document_id)
    document.status = IngestStatus.FAILED
    document.error_msg = error_message
    await session.commit()
    await session.refresh(document)
    await invalidate_knowledge_related_cache()
    return document


async def replace_document_chunks(
    session: AsyncSession,
    document_id: str,
    chunks: list[DocumentChunk],
) -> None:
    """Replace all chunks for a document."""

    await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    for chunk in chunks:
        session.add(chunk)
    await session.commit()


async def delete_document_record(session: AsyncSession, document_id: str) -> Document:
    """Delete a document record and its chunks."""

    document = await get_document_or_404(session, document_id)
    await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await session.delete(document)
    await session.commit()
    await invalidate_knowledge_related_cache()
    return document


async def build_knowledge_stats(session: AsyncSession) -> KnowledgeStatsResponse:
    """Build knowledge base statistics."""

    total_documents = int((await session.execute(select(func.count()).select_from(Document))).scalar_one())
    chunk_total_stmt = select(func.coalesce(func.sum(Document.chunk_count), 0)).select_from(Document)
    total_chunks = int(
        (await session.execute(chunk_total_stmt)).scalar_one()
    )
    processing_documents = int(
        (
            await session.execute(
                select(func.count())
                .select_from(Document)
                .where(Document.status.in_([IngestStatus.PENDING, IngestStatus.PROCESSING]))
            )
        ).scalar_one()
    )
    rows = (
        await session.execute(
            select(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type).order_by(Document.doc_type)
        )
    ).all()
    return KnowledgeStatsResponse(
        total_documents=total_documents,
        total_chunks=total_chunks,
        by_type=[{"name": str(doc_type), "value": int(count)} for doc_type, count in rows],
        processing_documents=processing_documents,
    )


async def invalidate_knowledge_related_cache() -> None:
    """Clear cached knowledge/dashboard stats after document changes."""

    cache = get_cache()
    await cache.delete("stats:knowledge")
    await cache.delete("stats:dashboard")


def remove_file_if_exists(path: str) -> None:
    """Delete a file from local storage if it still exists."""

    file_path = Path(path)
    if file_path.exists():
        file_path.unlink()
