"""Tests for Server-Sent Events framing helpers."""

from __future__ import annotations

from app.api.v1.chat import _sse_heartbeat, _sse_payload


def test_sse_payload_uses_named_event_and_compact_json() -> None:
    """SSE payloads should include an event name and JSON data frame."""

    assert _sse_payload({"type": "chunk", "content": "你好"}) == (
        'event: chunk\ndata: {"type":"chunk","content":"你好"}\n\n'
    )


def test_sse_heartbeat_is_comment_frame() -> None:
    """Heartbeat frames should be ignored by EventSource message handlers."""

    assert _sse_heartbeat() == ": ping\n\n"
