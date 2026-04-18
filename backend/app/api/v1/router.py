"""Aggregate API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import chat, events, knowledge, residents, stats

api_router = APIRouter()
api_router.include_router(chat.router)
api_router.include_router(events.router)
api_router.include_router(knowledge.router)
api_router.include_router(residents.router)
api_router.include_router(stats.router)

