"""Long-term memory helpers for chat sessions."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.chat_history import ChatMemory
from app.schemas.memory import MemoryDeleteResponse, MemoryItem

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

MEMORY_SCOPE_SESSION_PREFIX = "__gridrag_memory_scope__:"


class MemoryScope(StrEnum):
    """Supported memory scopes, ordered like layered configuration files."""

    ORGANIZATION = "organization"
    PROJECT = "project"
    PERSONAL = "personal"
    LOCAL = "local"
    AUTO = "auto"
    SESSION = "session"


HUMAN_RULE_SCOPES = (
    MemoryScope.ORGANIZATION,
    MemoryScope.PROJECT,
    MemoryScope.PERSONAL,
    MemoryScope.LOCAL,
)

MEMORY_SCOPE_ORDER = (*HUMAN_RULE_SCOPES, MemoryScope.AUTO, MemoryScope.SESSION)

MEMORY_SCOPE_LABELS = {
    MemoryScope.ORGANIZATION: "组织规则",
    MemoryScope.PROJECT: "项目规则",
    MemoryScope.PERSONAL: "个人偏好",
    MemoryScope.LOCAL: "本地规则",
    MemoryScope.AUTO: "自动经验",
    MemoryScope.SESSION: "会话记忆",
}

AUTO_MEMORY_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("project_pattern", ("本项目", "这个项目", "项目约定", "团队规范", "统一使用", "默认使用")),
    ("debug_experience", ("排查", "调试", "解决办法", "根因", "原因是", "以后遇到", "踩坑")),
    ("preference", ("偏好", "习惯", "称呼", "默认", "以后回答", "下次回答", "常用")),
)


def normalize_memory_scope(value: str | MemoryScope | None, default: MemoryScope = MemoryScope.SESSION) -> MemoryScope:
    """Normalize external scope input into a known memory scope."""

    if isinstance(value, MemoryScope):
        return value
    if not isinstance(value, str) or not value.strip():
        return default
    try:
        return MemoryScope(value.strip().lower())
    except ValueError:
        return default


def scoped_session_id(scope: str | MemoryScope) -> str:
    """Return the reserved session id used to persist a scoped memory layer."""

    normalized = normalize_memory_scope(scope)
    if normalized is MemoryScope.SESSION:
        raise ValueError("session scope does not use a reserved session id")
    return f"{MEMORY_SCOPE_SESSION_PREFIX}{normalized.value}"


def memory_scope(memory: ChatMemory) -> MemoryScope:
    """Resolve the effective scope for a persisted memory row."""

    metadata = memory.metadata_json or {}
    metadata_scope = metadata.get("scope")
    if isinstance(metadata_scope, str):
        return normalize_memory_scope(metadata_scope)
    if memory.session_id.startswith(MEMORY_SCOPE_SESSION_PREFIX):
        return normalize_memory_scope(memory.session_id.removeprefix(MEMORY_SCOPE_SESSION_PREFIX))
    return MemoryScope.SESSION


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
    scope: str | MemoryScope | None = None,
    key: str | None = None,
) -> ChatMemory:
    """Persist a memory, updating an exact duplicate when one already exists."""

    normalized_content = re.sub(r"\s+", " ", content).strip()
    metadata_json = dict(metadata or {})
    effective_scope = normalize_memory_scope(scope or _metadata_scope(metadata_json))
    if effective_scope is not MemoryScope.SESSION:
        session_id = scoped_session_id(effective_scope)
        metadata_json["scope"] = effective_scope.value

    memory_key = _normalize_memory_key(key or _metadata_key(metadata_json))
    if memory_key:
        metadata_json["key"] = memory_key

    existing = await _find_existing_memory(session, session_id, normalized_content, memory_key)
    if existing is not None:
        existing.content = normalized_content
        existing.memory_type = memory_type
        existing.metadata_json = {**existing.metadata_json, **metadata_json}
        existing.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(existing)
        return existing

    memory = ChatMemory(
        session_id=session_id,
        content=normalized_content,
        memory_type=memory_type,
        metadata_json=metadata_json,
    )
    session.add(memory)
    await session.commit()
    await session.refresh(memory)
    return memory


async def _find_existing_memory(
    session: AsyncSession,
    session_id: str,
    content: str,
    key: str | None,
) -> ChatMemory | None:
    """Find a row that should be updated instead of duplicated."""

    if key:
        result = await session.execute(select(ChatMemory).where(ChatMemory.session_id == session_id))
        for memory in result.scalars().all():
            if _normalize_memory_key(_metadata_key(memory.metadata_json or {})) == key:
                return memory
        return None

    existing = (
        await session.execute(
            select(ChatMemory).where(
                ChatMemory.session_id == session_id,
                ChatMemory.content == content,
            )
        )
    ).scalar_one_or_none()
    return existing


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
    category = classify_auto_memory(normalized)
    memory_content = _clean_memory_content(normalized)
    return await save_memory(
        session=session,
        session_id=session_id,
        content=memory_content,
        memory_type="auto",
        metadata={"source": "chat", "original_session_id": session_id, "category": category},
        scope=MemoryScope.AUTO,
        key=_auto_memory_key(category, memory_content),
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
    scoped_session_ids = [scoped_session_id(scope) for scope in (*HUMAN_RULE_SCOPES, MemoryScope.AUTO)]
    result = await session.execute(
        select(ChatMemory)
        .where(ChatMemory.session_id.in_([session_id, *scoped_session_ids]))
        .order_by(ChatMemory.updated_at.desc())
        .limit(settings.memory_max_items + 64)
    )
    memories = list(result.scalars().all())
    if not memories:
        return []

    rule_memories = _select_rule_memories(memories)
    dynamic_memories = [memory for memory in memories if memory_scope(memory) not in HUMAN_RULE_SCOPES]
    ranked = sorted(
        ((memory, _memory_score(query, memory.content)) for memory in dynamic_memories),
        key=lambda item: (item[1], item[0].updated_at),
        reverse=True,
    )
    positive = [memory for memory, score in ranked if score > 0]
    fallback_dynamic = dynamic_memories[: min(2, effective_limit)]
    selected = [*rule_memories, *((positive or fallback_dynamic)[:effective_limit])]
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

    settings = get_settings()
    effective_limit = max(1, min(limit or settings.memory_max_items, settings.memory_max_items))
    if query.strip():
        return await find_relevant_memories(
            session,
            session_id=session_id,
            query=query,
            limit=effective_limit,
            mark_used=False,
        )
    result = await session.execute(
        select(ChatMemory)
        .where(ChatMemory.session_id == session_id)
        .order_by(ChatMemory.updated_at.desc())
        .limit(effective_limit)
    )
    return list(result.scalars().all())


async def list_scoped_memories(
    session: AsyncSession,
    scope: str | MemoryScope,
    query: str = "",
    limit: int | None = None,
) -> list[ChatMemory]:
    """List memories stored in a reserved scope layer."""

    return await list_memories(session, session_id=scoped_session_id(scope), query=query, limit=limit)


async def delete_memory(session: AsyncSession, memory_id: str) -> bool:
    """Delete a memory by id."""

    result = await session.execute(delete(ChatMemory).where(ChatMemory.id == memory_id))
    await session.commit()
    return bool(_result_rowcount(result))


async def delete_session_memories(session: AsyncSession, session_id: str) -> MemoryDeleteResponse:
    """Delete all memories in one chat session."""

    result = await session.execute(delete(ChatMemory).where(ChatMemory.session_id == session_id))
    await session.commit()
    return MemoryDeleteResponse(session_id=session_id, deleted=_result_rowcount(result))


def render_memory_context(memories: list[ChatMemory]) -> list[str]:
    """Render memory rows into concise prompt snippets with layered overrides."""

    rule_candidates = [memory for memory in memories if memory_scope(memory) in HUMAN_RULE_SCOPES]
    selected_rules = _collapse_rule_memories(rule_candidates)
    dynamic = _dedupe_dynamic_memories([memory for memory in memories if memory_scope(memory) not in HUMAN_RULE_SCOPES])

    snippets: list[str] = []
    for memory in [*selected_rules, *dynamic]:
        scope = memory_scope(memory)
        label = MEMORY_SCOPE_LABELS[scope]
        category = _memory_category(memory)
        suffix = f"/{category}" if scope is MemoryScope.AUTO and category else ""
        snippets.append(f"{label}{suffix}：{_compact_memory_text(memory.content)}")
    return snippets


def _clean_memory_content(content: str) -> str:
    """Trim common explicit-memory prefixes without changing the user fact."""

    cleaned = re.sub(r"^(请)?记住[：:\s]*", "", content).strip()
    cleaned = re.sub(r"^以后[，,]?", "", cleaned).strip()
    return cleaned or content


def classify_auto_memory(content: str) -> str:
    """Classify a user-provided memory into a compact auto-memory category."""

    for category, triggers in AUTO_MEMORY_PATTERNS:
        if any(trigger in content for trigger in triggers):
            return category
    return "note"


def _select_rule_memories(memories: list[ChatMemory]) -> list[ChatMemory]:
    """Select a small set of human-authored rule memories from each scope."""

    selected: list[ChatMemory] = []
    for scope in HUMAN_RULE_SCOPES:
        scope_items = [memory for memory in memories if memory_scope(memory) is scope]
        selected.extend(scope_items[:8])
    return selected


def _collapse_rule_memories(memories: list[ChatMemory]) -> list[ChatMemory]:
    """Apply Git-style key override: more specific rule scopes replace broader ones."""

    by_key: dict[str, ChatMemory] = {}
    for memory in sorted(memories, key=lambda item: MEMORY_SCOPE_ORDER.index(memory_scope(item))):
        by_key[_memory_key(memory)] = memory
    return sorted(by_key.values(), key=lambda item: MEMORY_SCOPE_ORDER.index(memory_scope(item)))


def _dedupe_dynamic_memories(memories: list[ChatMemory]) -> list[ChatMemory]:
    """Drop duplicate dynamic memories after rule memories have been resolved."""

    seen: set[str] = set()
    selected: list[ChatMemory] = []
    for memory in memories:
        key = _memory_key(memory)
        if key in seen:
            continue
        seen.add(key)
        selected.append(memory)
    return selected


def _memory_key(memory: ChatMemory) -> str:
    """Return the override key for a memory row."""

    metadata_key = _normalize_memory_key(_metadata_key(memory.metadata_json or {}))
    if metadata_key:
        return metadata_key
    return _normalize_memory_key(memory.content) or memory.content[:80]


def _metadata_scope(metadata: dict[str, Any]) -> str | None:
    """Read a scope string from metadata."""

    value = metadata.get("scope")
    return value if isinstance(value, str) else None


def _metadata_key(metadata: dict[str, Any]) -> str | None:
    """Read a key string from metadata."""

    value = metadata.get("key")
    return value if isinstance(value, str) else None


def _normalize_memory_key(value: str | None) -> str | None:
    """Normalize override and dedupe keys."""

    if not value:
        return None
    normalized = re.sub(r"\s+", " ", value).strip().casefold()
    return normalized or None


def _memory_category(memory: ChatMemory) -> str:
    """Return the optional auto-memory category."""

    category = (memory.metadata_json or {}).get("category")
    return str(category).strip() if category else ""


def _auto_memory_key(category: str, content: str) -> str:
    """Build a stable key for cross-session auto memories."""

    return f"{category}:{_normalize_memory_key(content) or content[:80]}"


def _compact_memory_text(content: str, max_length: int = 180) -> str:
    """Keep injected memory compact to avoid context growth."""

    normalized = re.sub(r"\s+", " ", content).strip()
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 1]}…"


def _result_rowcount(result: object) -> int:
    """Read rowcount from SQLAlchemy delete results without depending on a concrete result type."""

    return int(getattr(result, "rowcount", 0) or 0)


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
