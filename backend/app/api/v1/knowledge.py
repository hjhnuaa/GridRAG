"""Knowledge base endpoints."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.exceptions import AppError
from app.ingest.tasks import trigger_document_ingestion
from app.models.enums import DocType
from app.rag.store import get_chroma_store
from app.schemas.common import ApiResponse, success_response
from app.schemas.document import DocumentResponse
from app.services.documents import (
    build_knowledge_stats,
    create_document_record,
    delete_document_record,
    get_document_or_404,
    invalidate_knowledge_related_cache,
    list_documents,
    remove_file_if_exists,
)

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


@router.get("/documents")
async def get_documents(
    page: int = 1,
    page_size: int = 20,
    doc_type: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """List uploaded documents."""

    data = await list_documents(session=session, page=page, page_size=page_size, doc_type=doc_type)
    return success_response(data)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: dict[str, object] = Depends(get_current_user),
) -> ApiResponse[DocumentResponse]:
    """Upload a document and queue indexing."""

    settings = get_settings()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".xlsx", ".csv"}:
        raise AppError("仅支持上传 PDF、DOCX、TXT、XLSX、CSV 文档。", code=4004)
    target_name = f"{uuid4()}{suffix}"
    target_path = settings.upload_path / target_name
    file_bytes = await file.read()
    async with aiofiles.open(target_path, "wb") as output:
        await output.write(file_bytes)

    try:
        normalized_doc_type = DocType(doc_type)
    except ValueError as exc:
        raise AppError("文档类型无效。", code=4005) from exc

    document = await create_document_record(
        session=session,
        name=file.filename or target_name,
        doc_type=normalized_doc_type,
        file_path=str(target_path),
        file_size=len(file_bytes),
        uploaded_by=str(current_user.get("username", "系统")),
    )
    background_tasks.add_task(trigger_document_ingestion, document.id)
    return success_response(DocumentResponse.model_validate(document))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Delete a document and its vector index."""

    document = await get_document_or_404(session, document_id)
    get_chroma_store().delete_document(document.id, str(document.doc_type))
    remove_file_if_exists(document.file_path)
    deleted_document = await delete_document_record(session, document_id)
    return success_response({"id": deleted_document.id})


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Queue a reindex task for a document."""

    document = await get_document_or_404(session, document_id)
    await invalidate_knowledge_related_cache()
    background_tasks.add_task(trigger_document_ingestion, document.id)
    return success_response({"id": document.id, "status": "PROCESSING"})


@router.get("/stats")
async def knowledge_stats(
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Return knowledge base statistics."""

    data = await build_knowledge_stats(session)
    return success_response(data.model_dump())
