"""Tests for layered memory rendering."""

from __future__ import annotations

import pytest

from app.models.chat_history import ChatMemory
from app.services.memory import MemoryScope, classify_auto_memory, render_memory_context, scoped_session_id


def _memory(
    scope: MemoryScope,
    content: str,
    *,
    key: str | None = None,
    memory_type: str = "rule",
) -> ChatMemory:
    metadata: dict[str, str] = {}
    if scope is MemoryScope.SESSION:
        session_id = "session-1"
    else:
        session_id = scoped_session_id(scope)
        metadata["scope"] = scope.value
    if key:
        metadata["key"] = key
    return ChatMemory(session_id=session_id, content=content, memory_type=memory_type, metadata_json=metadata)


def test_render_memory_context_applies_scope_override_by_key() -> None:
    """More specific rule scopes should replace broader rules with the same key."""

    snippets = render_memory_context(
        [
            _memory(MemoryScope.ORGANIZATION, "回答保持正式书面语。", key="tone"),
            _memory(MemoryScope.PROJECT, "回答使用简洁口语化表达。", key="tone"),
            _memory(MemoryScope.LOCAL, "本地调试默认先看 RAG Debug。", key="debug"),
            _memory(MemoryScope.AUTO, "低保问题优先核对材料清单。", memory_type="auto"),
            _memory(MemoryScope.SESSION, "当前用户负责朝阳社区。", memory_type="manual"),
        ]
    )

    assert not any("回答保持正式书面语" in item for item in snippets)
    assert "项目规则：回答使用简洁口语化表达。" in snippets
    assert "本地规则：本地调试默认先看 RAG Debug。" in snippets
    assert "自动经验：低保问题优先核对材料清单。" in snippets
    assert "会话记忆：当前用户负责朝阳社区。" in snippets


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("请记住我的偏好是回答要短。", "preference"),
        ("本项目默认使用政策原文作为依据。", "project_pattern"),
        ("以后遇到召回异常先排查重排分数。", "debug_experience"),
        ("请记住朝阳社区属于第一网格。", "note"),
    ],
)
def test_classify_auto_memory(content: str, expected: str) -> None:
    """Auto memories should be grouped by useful operational category."""

    assert classify_auto_memory(content) == expected


def test_scoped_session_id_rejects_session_scope() -> None:
    """Session memories keep their real session id instead of a reserved scoped id."""

    with pytest.raises(ValueError):
        scoped_session_id(MemoryScope.SESSION)
