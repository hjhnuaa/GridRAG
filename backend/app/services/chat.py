"""Service functions for chat sessions, history, and retrieval logs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_history import ChatHistory, ChatMemory, ChatSession, RetrievalLog
from app.schemas.chat import ChatMessage, ChatSessionDeleteResponse, ChatSessionSummary
from app.schemas.common import PaginatedData, PaginationMeta

DEFAULT_SESSION_TITLE = "新会话"
SESSION_TITLE_PREVIEW_LENGTH = 24


def build_session_title(content: str) -> str:
    """Build a compact default session title from the first user message."""

    title = " ".join(content.split()).strip()
    return title[:SESSION_TITLE_PREVIEW_LENGTH] or DEFAULT_SESSION_TITLE


def _serialize_chat_session(item: ChatSession) -> ChatSessionSummary:
    """Convert a chat session ORM object into an API schema."""

    return ChatSessionSummary(
        id=item.id,
        title=item.title,
        message_count=item.message_count,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


async def _ensure_chat_session(
    session: AsyncSession,
    session_id: str,
    title: str | None = None,
) -> ChatSession:
    """Ensure a session metadata row exists without committing."""

    chat_session = await session.get(ChatSession, session_id)
    normalized_title = title.strip() if title else ""
    if chat_session is not None:
        if normalized_title and chat_session.title == DEFAULT_SESSION_TITLE:
            chat_session.title = normalized_title[:120]
        return chat_session

    now = datetime.now(UTC)
    chat_session = ChatSession(
        id=session_id,
        title=(normalized_title[:120] if normalized_title else DEFAULT_SESSION_TITLE),
        message_count=0,
        created_at=now,
        updated_at=now,
    )
    session.add(chat_session)
    return chat_session


async def create_chat_session(
    session: AsyncSession,
    session_id: str | None = None,
    title: str | None = None,
) -> ChatSessionSummary:
    """Create a session metadata row or return the existing one."""

    target_session_id = session_id.strip() if session_id else ""
    if not target_session_id:
        target_session_id = str(uuid4())
    chat_session = await _ensure_chat_session(session, target_session_id, title=title)
    await session.commit()
    await session.refresh(chat_session)
    return _serialize_chat_session(chat_session)


async def list_chat_sessions(
    session: AsyncSession,
    page: int,
    page_size: int,
) -> PaginatedData[ChatSessionSummary]:
    """List persisted chat sessions by latest activity."""

    stmt = select(ChatSession).order_by(ChatSession.updated_at.desc())
    count_stmt = select(func.count()).select_from(ChatSession)
    total = int((await session.execute(count_stmt)).scalar_one())
    sessions = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedData(
        items=[_serialize_chat_session(item) for item in sessions],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


async def update_chat_session_title(session: AsyncSession, session_id: str, title: str) -> ChatSessionSummary:
    """Update a chat session title."""

    chat_session = await _ensure_chat_session(session, session_id)
    chat_session.title = title.strip()[:120] or DEFAULT_SESSION_TITLE
    chat_session.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(chat_session)
    return _serialize_chat_session(chat_session)


async def save_chat_message(
    session: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    sources: list[dict[str, str | int | float | None]] | None = None,
) -> ChatHistory:
    """Persist a chat message and update its session metadata."""

    now = datetime.now(UTC)
    chat_session = await _ensure_chat_session(session, session_id)
    if role == "user" and (chat_session.message_count == 0 or chat_session.title == DEFAULT_SESSION_TITLE):
        chat_session.title = build_session_title(content)
    chat_session.message_count += 1
    chat_session.updated_at = now

    message = ChatHistory(session_id=session_id, role=role, content=content, sources=sources, created_at=now)
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


async def delete_chat_session(session: AsyncSession, session_id: str) -> ChatSessionDeleteResponse:
    """Delete one chat session and its diagnostic data."""

    memory_result = await session.execute(delete(ChatMemory).where(ChatMemory.session_id == session_id))
    log_result = await session.execute(delete(RetrievalLog).where(RetrievalLog.session_id == session_id))
    message_result = await session.execute(delete(ChatHistory).where(ChatHistory.session_id == session_id))
    await session.execute(delete(ChatSession).where(ChatSession.id == session_id))
    await session.commit()
    return ChatSessionDeleteResponse(
        session_id=session_id,
        deleted_messages=int(message_result.rowcount or 0),
        deleted_retrieval_logs=int(log_result.rowcount or 0),
        deleted_memories=int(memory_result.rowcount or 0),
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
