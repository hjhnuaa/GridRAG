"""Long-term memory helpers for chat sessions."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.chat_history import ChatMemory
from app.schemas.memory import MemoryItem

MEMORY_TRIGGERS = (
    "记住",
    "请记住",
    "以后",
    "下次",
    "偏好",
    "习惯",
    "称呼",
    "默认",
    "我负责",
    "我的职责",
    "常用",
)


def to_memory_item(memory: ChatMemory) -> MemoryItem:
    """Convert an ORM memory object to an API schema."""

    return MemoryItem(
        id=memory.id,
        session_id=memory.session_id,
        content=memory.content,
        memory_type=memory.memory_type,
        metadata=memory.metadata_json,
        usage_count=memory.usage_count,
        last_used_at=memory.last_used_at.isoformat() if memory.last_used_at else None,
        created_at=memory.created_at.isoformat(),
        updated_at=memory.updated_at.isoformat(),
    )


async def save_memory(
    session: AsyncSession,
    session_id: str,
    content: str,
    memory_type: str = "note",
    metadata: dict[str, Any] | None = None,
) -> ChatMemory:
    """Persist a memory, updating an exact duplicate when one already exists."""

    normalized_content = re.sub(r"\s+", " ", content).strip()
    existing = (
        await session.execute(
            select(ChatMemory).where(
                ChatMemory.session_id == session_id,
                ChatMemory.content == normalized_content,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.memory_type = memory_type
        existing.metadata_json = metadata or existing.metadata_json
        existing.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(existing)
        return existing

    memory = ChatMemory(
        session_id=session_id,
        content=normalized_content,
        memory_type=memory_type,
        metadata_json=metadata or {},
    )
    session.add(memory)
    await session.commit()
    await session.refresh(memory)
    return memory


async def maybe_save_user_memory(session: AsyncSession, session_id: str, content: str) -> ChatMemory | None:
    """Store user-provided memory when the message explicitly asks to remember something."""

    settings = get_settings()
    normalized = re.sub(r"\s+", " ", content).strip()
    if not settings.memory_enabled or not settings.memory_auto_save:
        return None
    if len(normalized) < settings.memory_min_content_length:
        return None
    if not any(trigger in normalized for trigger in MEMORY_TRIGGERS):
        return None
    return await save_memory(
        session=session,
        session_id=session_id,
        content=_clean_memory_content(normalized),
        memory_type="auto",
        metadata={"source": "chat"},
    )


async def find_relevant_memories(
    session: AsyncSession,
    session_id: str,
    query: str = "",
    limit: int | None = None,
    mark_used: bool = True,
) -> list[ChatMemory]:
    """Return the most relevant memories for a question."""

    settings = get_settings()
    if not settings.memory_enabled:
        return []

    effective_limit = limit or settings.memory_relevance_limit
    result = await session.execute(
        select(ChatMemory)
        .where(ChatMemory.session_id == session_id)
        .order_by(ChatMemory.updated_at.desc())
        .limit(settings.memory_max_items)
    )
    memories = list(result.scalars().all())
    if not memories:
        return []

    ranked = sorted(
        ((memory, _memory_score(query, memory.content)) for memory in memories),
        key=lambda item: (item[1], item[0].updated_at),
        reverse=True,
    )
    positive = [memory for memory, score in ranked if score > 0]
    selected = (positive or memories[: min(2, effective_limit)])[:effective_limit]
    if selected and mark_used:
        now = datetime.now(UTC)
        for memory in selected:
            memory.usage_count += 1
            memory.last_used_at = now
            memory.updated_at = now
        await session.commit()
    return selected


async def list_memories(
    session: AsyncSession,
    session_id: str,
    query: str = "",
    limit: int | None = None,
) -> list[ChatMemory]:
    """List or search memories for a session."""

    if query.strip():
        return await find_relevant_memories(
            session,
            session_id=session_id,
            query=query,
            limit=limit,
            mark_used=False,
        )
    settings = get_settings()
    result = await session.execute(
        select(ChatMemory)
        .where(ChatMemory.session_id == session_id)
        .order_by(ChatMemory.updated_at.desc())
        .limit(limit or settings.memory_max_items)
    )
    return list(result.scalars().all())


async def delete_memory(session: AsyncSession, memory_id: str) -> bool:
    """Delete a memory by id."""

    result = await session.execute(delete(ChatMemory).where(ChatMemory.id == memory_id))
    await session.commit()
    return bool(result.rowcount)


def render_memory_context(memories: list[ChatMemory]) -> list[str]:
    """Render memory rows into concise prompt snippets."""

    return [memory.content for memory in memories]


def _clean_memory_content(content: str) -> str:
    """Trim common explicit-memory prefixes without changing the user fact."""

    return re.sub(r"^(请)?记住[：:\s]*", "", content).strip() or content


def _memory_score(query: str, content: str) -> float:
    """Score memory relevance with lightweight lexical overlap."""

    query_terms = _terms(query)
    content_terms = _terms(content)
    if not query_terms:
        return 0.0
    overlap = len(query_terms & content_terms)
    phrase_bonus = 1.0 if query.strip() and query.strip() in content else 0.0
    return overlap / max(len(query_terms), 1) + phrase_bonus


def _terms(text: str) -> set[str]:
    """Extract coarse terms from Chinese and Latin text."""

    lowered = text.casefold()
    words = {item for item in re.findall(r"[a-z0-9_]{2,}", lowered)}
    chinese_chars = {char for char in lowered if "\u4e00" <= char <= "\u9fff"}
    return words | chinese_chars
