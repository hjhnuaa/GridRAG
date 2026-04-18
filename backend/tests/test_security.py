"""Tests for JWT helpers."""

from __future__ import annotations

from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_access_token() -> None:
    """JWT tokens should round-trip."""

    token = create_access_token("grid-user")
    payload = decode_access_token(token)
    assert payload["sub"] == "grid-user"

