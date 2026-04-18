"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.cache import RedisCache, get_cache
from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.rag.pipeline import RAGPipeline

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Return the current user from the JWT token or a development stub."""

    if settings.auth_disabled:
        return {"username": "开发环境用户", "role": "admin"}
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少登录凭证。")
    payload = decode_access_token(credentials.credentials)
    return {
        "username": payload.get("sub", ""),
        "role": payload.get("role", "user"),
    }


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    """Return the singleton RAG pipeline."""

    return RAGPipeline()


def get_cache_dependency() -> RedisCache:
    """Return the Redis cache wrapper."""

    return get_cache()

