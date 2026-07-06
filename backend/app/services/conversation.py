"""Conversation context helpers for multi-turn chat."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.chat_history import ChatHistory, ChatSession

logger = get_logger(__name__)


@dataclass(frozen=True)
class ConversationContext:
    """Prompt-ready conversation context."""

    snippets: list[str]
    summary: str | None
    fingerprint: str


def _role_label(role: str) -> str:
    if role == "assistant":
        return "助手"
    if role == "user":
        return "用户"
    return role


def _trim_text(text: str, limit: int) -> str:
    normalized = " ".join(text.split()).strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


def render_history_snippet(message: ChatHistory, *, content_limit: int = 420) -> str:
    """Render one chat history row for prompt context."""

    suffix = "（已中断）" if message.status == "interrupted" else ""
    return f"{_role_label(message.role)}{suffix}：{_trim_text(message.content, content_limit)}"


async def get_recent_history(
    session: AsyncSession,
    session_id: str,
    *,
    limit: int | None = None,
    exclude_latest_user: bool = False,
) -> list[ChatHistory]:
    """Return recent chat history in chronological order."""

    settings = get_settings()
    effective_limit = limit or settings.conversation_recent_turns * 2
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(effective_limit + (1 if exclude_latest_user else 0))
    )
    messages = list((await session.execute(stmt)).scalars().all())
    messages.reverse()
    if exclude_latest_user:
        for index in range(len(messages) - 1, -1, -1):
            if messages[index].role == "user":
                del messages[index]
                break
    return messages[-effective_limit:]


async def build_conversation_context(
    session: AsyncSession,
    session_id: str,
    *,
    exclude_latest_user: bool = False,
) -> ConversationContext:
    """Build summary and recent-turn snippets for prompt injection."""

    settings = get_settings()
    chat_session = await session.get(ChatSession, session_id)
    recent_messages = await get_recent_history(
        session,
        session_id,
        limit=settings.conversation_recent_turns * 2,
        exclude_latest_user=exclude_latest_user,
    )
    snippets: list[str] = []
    total_chars = 0
    for message in recent_messages:
        snippet = render_history_snippet(message)
        if snippets and total_chars + len(snippet) > settings.conversation_context_max_chars:
            break
        snippets.append(snippet)
        total_chars += len(snippet)
    summary = (
        _trim_text(chat_session.summary, settings.conversation_summary_max_chars)
        if chat_session is not None and chat_session.summary
        else None
    )
    fingerprint = "\n".join([summary or "", *snippets])
    return ConversationContext(snippets=snippets, summary=summary, fingerprint=fingerprint)


async def maybe_update_conversation_summary(
    session: AsyncSession,
    session_id: str,
    *,
    generator: object,
) -> str | None:
    """Update a compact conversation summary when the session grows long enough."""

    settings = get_settings()
    chat_session = await session.get(ChatSession, session_id)
    if chat_session is None:
        return None
    if chat_session.message_count < settings.conversation_summary_trigger_messages:
        return chat_session.summary
    if chat_session.summary_message_count >= chat_session.message_count:
        return chat_session.summary

    messages = await get_recent_history(
        session,
        session_id,
        limit=settings.conversation_summary_trigger_messages,
        exclude_latest_user=False,
    )
    rendered_history = [render_history_snippet(item, content_limit=520) for item in messages]
    render_prompt = getattr(generator, "render_prompt")
    generate_text = getattr(generator, "generate_text")
    prompt = render_prompt(
        "conversation_summary.j2",
        previous_summary=chat_session.summary or "",
        messages=rendered_history,
        max_chars=settings.conversation_summary_max_chars,
    )
    try:
        summary = _trim_text(await generate_text(prompt), settings.conversation_summary_max_chars)
    except Exception as exc:
        logger.warning("conversation_summary_failed", session_id=session_id, error=str(exc))
        return chat_session.summary
    if not summary:
        return chat_session.summary
    chat_session.summary = summary
    chat_session.summary_message_count = chat_session.message_count
    chat_session.summary_updated_at = datetime.now(UTC)
    await session.commit()
    return summary
