"""Tests for JWT helpers."""

from __future__ import annotations

from app.core.security import create_access_token, decode_access_token, mask_id_number, mask_phone


def test_create_and_decode_access_token() -> None:
    """JWT tokens should round-trip."""

    token = create_access_token("grid-user")
    payload = decode_access_token(token)
    assert payload["sub"] == "grid-user"


def test_mask_id_number() -> None:
    """ID numbers should only expose the last four characters."""

    assert mask_id_number("123456789012345678") == "**************5678"


def test_mask_phone() -> None:
    """Phone numbers should hide middle digits."""

    assert mask_phone("13812345678") == "138****5678"
