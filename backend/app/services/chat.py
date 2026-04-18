"""Service functions for chat history and retrieval logs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_history import ChatHistory, RetrievalLog
from app.schemas.chat import ChatMessage
from app.schemas.common import PaginatedData, PaginationMeta


async def save_chat_message(
    session: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    sources: list[dict[str, str | int | float | None]] | None = None,
) -> ChatHistory:
    """Persist a chat message."""

    message = ChatHistory(session_id=session_id, role=role, content=content, sources=sources)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def list_chat_history(
    session: AsyncSession,
    session_id: str,
    page: int,
    page_size: int,
) -> PaginatedData[ChatMessage]:
    """List paginated chat history."""

    stmt = select(ChatHistory).where(ChatHistory.session_id == session_id).order_by(ChatHistory.created_at.asc())
    count_stmt = select(func.count()).select_from(ChatHistory).where(ChatHistory.session_id == session_id)
    total = int((await session.execute(count_stmt)).scalar_one())
    messages = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedData(
        items=[
            ChatMessage(
                id=item.id,
                session_id=item.session_id,
                role=item.role,
                content=item.content,
                sources=item.sources,  # type: ignore[arg-type]
                created_at=item.created_at.isoformat(),
            )
            for item in messages
        ],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


async def save_retrieval_log(
    session: AsyncSession,
    session_id: str,
    query: str,
    rewritten_query: str | None,
    filters: dict[str, str | list[str] | None],
    retrieval_ms: int,
    rerank_scores: list[dict[str, str | float | int | None]],
    top_chunks: list[dict[str, str | float | int | None]],
    is_grounded: bool,
) -> RetrievalLog:
    """Persist a retrieval log entry."""

    log = RetrievalLog(
        session_id=session_id,
        query=query,
        rewritten_query=rewritten_query,
        filters=filters,
        retrieval_ms=retrieval_ms,
        rerank_scores=rerank_scores,
        top_chunks=top_chunks,
        is_grounded=is_grounded,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log
