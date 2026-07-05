"""Server-Sent Events framing and streaming helpers."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, AsyncIterable
from contextlib import suppress
from typing import TypeAlias

from fastapi import Request

SSE_HEARTBEAT_SECONDS = 10.0
SSE_QUEUE_MAX_SIZE = 32
SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}
SSEEvent: TypeAlias = dict[str, object]


class _StreamEnd:
    """Sentinel for the end of the producer task."""


_STREAM_END = _StreamEnd()


def _sse_payload(data: SSEEvent) -> str:
    """Format an SSE event."""

    event_type = str(data.get("type", "message"))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_type}\ndata: {payload}\n\n"


def _sse_heartbeat() -> str:
    """Return an SSE comment heartbeat that clients ignore."""

    return ": ping\n\n"


async def stream_sse_events(
    request: Request,
    events: AsyncIterable[SSEEvent],
    *,
    task_name: str,
    heartbeat_seconds: float = SSE_HEARTBEAT_SECONDS,
    queue_max_size: int = SSE_QUEUE_MAX_SIZE,
) -> AsyncGenerator[str, None]:
    """Yield framed SSE events from an async event iterable."""

    queue: asyncio.Queue[SSEEvent | _StreamEnd] = asyncio.Queue(maxsize=queue_max_size)

    async def produce_events() -> None:
        try:
            async for event in events:
                await queue.put(event)
        finally:
            task = asyncio.current_task()
            if task is None or not task.cancelling():
                await queue.put(_STREAM_END)

    producer = asyncio.create_task(produce_events(), name=task_name)
    try:
        while True:
            if await request.is_disconnected():
                producer.cancel()
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
            except TimeoutError:
                yield _sse_heartbeat()
                continue
            if isinstance(event, _StreamEnd):
                break
            yield _sse_payload(event)
    finally:
        if not producer.done():
            producer.cancel()
        with suppress(asyncio.CancelledError):
            await producer
