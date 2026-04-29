"""Chat and RAG debug endpoints."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_rag_pipeline
from app.core.database import get_db_session
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.rag.pipeline import RAGPipeline
from app.schemas.chat import ChatAskRequest, ChatSessionCreateRequest, ChatSessionUpdateRequest
from app.schemas.common import ApiResponse, success_response
from app.services.chat import (
    create_chat_session,
    delete_chat_session,
    list_chat_history,
    list_chat_sessions,
    save_chat_message,
    update_chat_session_title,
)
from app.services.memory import maybe_save_user_memory

router = APIRouter(prefix="/chat", tags=["智能问答"])
logger = get_logger(__name__)


def _sse_payload(data: dict[str, object]) -> str:
    """Format an SSE event."""

    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/ask")
async def ask(
    payload: ChatAskRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: dict[str, object] = Depends(get_current_user),
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> StreamingResponse:
    """Stream a grounded answer via Server-Sent Events."""

    await save_chat_message(session, payload.session_id, "user", payload.question)
    await maybe_save_user_memory(session, payload.session_id, payload.question)

    async def event_stream() -> AsyncGenerator[str, None]:
        """Yield SSE events from the RAG pipeline."""

        try:
            async for event in pipeline.stream_answer(
                session=session,
                session_id=payload.session_id,
                question=payload.question,
                doc_types=payload.filters.doc_types,
                enable_web_search=payload.filters.enable_web_search,
            ):
                yield _sse_payload(event)
        except AppError as exc:
            logger.exception("chat_stream_app_error", error=exc.message, user=current_user.get("username"))
            yield _sse_payload({"type": "error", "message": exc.message})
            yield _sse_payload({"type": "done"})
        except Exception as exc:
            logger.exception("chat_stream_failed", error=str(exc), user=current_user.get("username"))
            yield _sse_payload({"type": "error", "message": "问答失败，请稍后重试。"})
            yield _sse_payload({"type": "done"})

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@router.post("/sessions")
async def create_session(
    payload: ChatSessionCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Create or ensure a persisted chat session."""

    data = await create_chat_session(session, session_id=payload.session_id, title=payload.title)
    return success_response(data)


@router.get("/sessions")
async def sessions(
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Return persisted chat sessions."""

    data = await list_chat_sessions(session, page=page, page_size=page_size)
    return success_response(data)


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    payload: ChatSessionUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Update a persisted chat session."""

    data = await update_chat_session_title(session, session_id=session_id, title=payload.title)
    return success_response(data)


@router.get("/history/{session_id}")
async def history(
    session_id: str,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Return paginated chat history."""

    data = await list_chat_history(session, session_id=session_id, page=page, page_size=page_size)
    return success_response(data)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Delete a chat session from persisted history."""

    data = await delete_chat_session(session, session_id)
    return success_response(data)


@router.post("/debug")
async def debug_chat(
    payload: ChatAskRequest,
    session: AsyncSession = Depends(get_db_session),
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> ApiResponse[object]:
    """Return a detailed RAG debug payload."""

    debug_payload = await pipeline.debug(
        session=session,
        session_id=payload.session_id,
        question=payload.question,
        doc_types=payload.filters.doc_types,
        enable_web_search=payload.filters.enable_web_search,
    )
    return success_response(debug_payload)
