"""Dashboard statistics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cache_dependency
from app.core.cache import RedisCache
from app.core.database import get_db_session
from app.schemas.common import ApiResponse, success_response
from app.services.stats import build_dashboard_stats

router = APIRouter(prefix="/stats", tags=["统计看板"])


@router.get("/dashboard")
async def dashboard(
    cache: RedisCache = Depends(get_cache_dependency),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Return dashboard statistics."""

    cached = await cache.get_json("stats:dashboard")
    if isinstance(cached, dict):
        return success_response(cached)

    data = await build_dashboard_stats(session)
    payload = data.model_dump()
    await cache.set_json("stats:dashboard", payload, ttl=300)
    return success_response(payload)

