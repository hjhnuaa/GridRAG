"""Tests for CORS preflight behavior."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import Settings


def test_local_vite_fallback_port_preflight_is_allowed() -> None:
    """Vite may fall back from 5173 to 5174 when the default port is occupied."""

    settings = Settings(_env_file=None)
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    client = TestClient(app)
    response = client.options(
        "/api/v1/chat/ask",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"


def test_blank_cors_origin_regex_is_disabled() -> None:
    """A blank regex should not accidentally match every origin."""

    settings = Settings(_env_file=None, cors_origin_regex="")

    assert settings.cors_origin_regex is None
