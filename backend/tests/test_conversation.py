"""Tests for multi-turn conversation context helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.chat_history import ChatHistory, ChatSession
from app.services.conversation import build_conversation_context, render_history_snippet


class _ScalarResult:
    def __init__(self, rows: list[ChatHistory]) -> None:
        self.rows = rows

    def all(self) -> list[ChatHistory]:
        return self.rows


class _ExecuteResult:
    def __init__(self, rows: list[ChatHistory]) -> None:
        self.rows = rows

    def scalars(self) -> _ScalarResult:
        return _ScalarResult(self.rows)


class FakeSession:
    def __init__(self, chat_session: ChatSession, messages: list[ChatHistory]) -> None:
        self.chat_session = chat_session
        self.messages = messages

    async def get(self, model: object, session_id: str) -> ChatSession | None:
        if model is ChatSession and session_id == self.chat_session.id:
            return self.chat_session
        return None

    async def execute(self, _: object) -> _ExecuteResult:
        return _ExecuteResult(list(reversed(self.messages)))


def _message(role: str, content: str, offset: int, status: str = "complete") -> ChatHistory:
    return ChatHistory(
        session_id="session-1",
        role=role,
        content=content,
        status=status,
        created_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=offset),
    )


def test_render_history_snippet_marks_interrupted_message() -> None:
    """Interrupted assistant answers should be visible in prompt context."""

    snippet = render_history_snippet(_message("assistant", "先回答了一半", 1, status="interrupted"))

    assert snippet == "助手（已中断）：先回答了一半"


@pytest.mark.asyncio
async def test_build_conversation_context_excludes_latest_user_message() -> None:
    """Context for /ask excludes the current user message already saved by the endpoint."""

    chat_session = ChatSession(
        id="session-1",
        title="低保咨询",
        message_count=3,
        summary="用户在咨询低保办理。",
        summary_message_count=2,
    )
    fake_session = FakeSession(
        chat_session,
        [
            _message("user", "低保怎么办？", 1),
            _message("assistant", "先核对申请条件。", 2),
            _message("user", "刚才那个还要什么材料？", 3),
        ],
    )

    context = await build_conversation_context(fake_session, "session-1", exclude_latest_user=True)  # type: ignore[arg-type]

    assert context.summary == "用户在咨询低保办理。"
    assert context.snippets == ["用户：低保怎么办？", "助手：先核对申请条件。"]
    assert "刚才那个还要什么材料" not in context.fingerprint
