"""Aggregate API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import chat, events, knowledge, mcp, memory, residents, stats, web_search

api_router = APIRouter()
api_router.include_router(chat.router)
api_router.include_router(events.router)
api_router.include_router(knowledge.router)
api_router.include_router(memory.router)
api_router.include_router(mcp.router)
api_router.include_router(residents.router)
api_router.include_router(stats.router)
api_router.include_router(web_search.router)
