"""JWT security helpers and authentication dependencies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


def create_access_token(subject: str, extra_payload: dict[str, Any] | None = None) -> str:
    """Create a signed JWT access token."""

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    if extra_payload:
        payload.update(extra_payload)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""

    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态无效，请重新登录。",
        ) from exc


def mask_id_number(value: str) -> str:
    """Mask an ID number, keeping only the last four characters visible."""

    cleaned = value.strip()
    if len(cleaned) <= 4:
        return cleaned
    return "*" * (len(cleaned) - 4) + cleaned[-4:]


def mask_phone(value: str) -> str:
    """Mask a phone number while preserving the last four digits."""

    cleaned = value.strip()
    if len(cleaned) <= 4:
        return cleaned
    # 手机号只保留前三位和后四位，避免居民隐私在列表页和日志中直接暴露。
    return f"{cleaned[:3]}****{cleaned[-4:]}"
