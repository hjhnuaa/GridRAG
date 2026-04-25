"""Configurable web search adapters."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import status

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.web_search import WebSearchResult

logger = get_logger(__name__)

DEFAULT_ENDPOINTS = {
    "bing": "https://api.bing.microsoft.com/v7.0/search",
    "serper": "https://google.serper.dev/search",
}


class WebSearchProviderError(AppError):
    """Normalized error returned by a third-party search provider."""

    def __init__(
        self,
        message: str,
        provider: str,
        provider_status_code: int | None = None,
        response_preview: str = "",
    ) -> None:
        """Initialize a provider error without storing secrets."""

        super().__init__(message=message, code=4104, status_code=status.HTTP_502_BAD_GATEWAY)
        self.provider = provider
        self.provider_status_code = provider_status_code
        self.response_preview = response_preview


class WebSearchService:
    """Run web searches through a configured provider."""

    async def search(self, query: str, max_results: int | None = None) -> list[WebSearchResult]:
        """Search the web and return normalized results."""

        settings = get_settings()
        if not settings.web_search_enabled:
            return []

        provider = normalize_provider(settings.web_search_provider)
        limit = max_results or settings.web_search_max_results
        timeout = httpx.Timeout(settings.web_search_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            if provider == "bing":
                return await self._search_bing(client, query, limit)
            if provider == "serper":
                return await self._search_serper(client, query, limit)
            return await self._search_searxng(client, query, limit)

    async def _search_searxng(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> list[WebSearchResult]:
        """Search a SearXNG-compatible JSON endpoint."""

        settings = get_settings()
        if not settings.web_search_endpoint:
            raise AppError("未配置 WEB_SEARCH_ENDPOINT，无法执行联网搜索。", code=4101)
        response = await client.get(
            settings.web_search_endpoint,
            params={"q": query, "format": "json", "language": "zh-CN"},
        )
        _raise_for_provider_status(response, "searxng")
        payload = response.json()
        raw_items = payload.get("results", []) if isinstance(payload, dict) else []
        return [
            WebSearchResult(
                title=str(item.get("title") or item.get("url") or "搜索结果"),
                url=str(item.get("url") or ""),
                snippet=str(item.get("content") or item.get("snippet") or ""),
                provider="searxng",
                score=float(item["score"]) if isinstance(item.get("score"), (int, float)) else None,
            )
            for item in raw_items[:limit]
            if isinstance(item, dict) and item.get("url")
        ]

    async def _search_bing(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> list[WebSearchResult]:
        """Search Bing Web Search API."""

        settings = get_settings()
        if not settings.web_search_api_key:
            raise AppError("未配置 BING_SEARCH_API_KEY 或 WEB_SEARCH_API_KEY。", code=4102)
        endpoint = resolve_provider_endpoint("bing", settings.web_search_endpoint)
        response = await client.get(
            endpoint,
            params={"q": query, "mkt": "zh-CN", "count": limit},
            headers={"Ocp-Apim-Subscription-Key": settings.web_search_api_key},
        )
        _raise_for_provider_status(response, "bing")
        payload = response.json()
        raw_items = payload.get("webPages", {}).get("value", []) if isinstance(payload, dict) else []
        return [
            WebSearchResult(
                title=str(item.get("name") or item.get("url") or "搜索结果"),
                url=str(item.get("url") or ""),
                snippet=str(item.get("snippet") or ""),
                provider="bing",
            )
            for item in raw_items[:limit]
            if isinstance(item, dict) and item.get("url")
        ]

    async def _search_serper(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> list[WebSearchResult]:
        """Search Google Serper API."""

        settings = get_settings()
        if not settings.web_search_api_key:
            raise AppError("未配置 SERPER_API_KEY 或 WEB_SEARCH_API_KEY。", code=4103)
        endpoint = resolve_provider_endpoint("serper", settings.web_search_endpoint)
        response = await client.post(
            endpoint,
            headers={"X-API-KEY": settings.web_search_api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "cn", "hl": "zh-cn", "num": limit},
        )
        _raise_for_provider_status(response, "serper")
        payload = response.json()
        raw_items = payload.get("organic", []) if isinstance(payload, dict) else []
        return [
            WebSearchResult(
                title=str(item.get("title") or item.get("link") or "搜索结果"),
                url=str(item.get("link") or ""),
                snippet=str(item.get("snippet") or ""),
                provider="serper",
                score=_position_to_score(item),
            )
            for item in raw_items[:limit]
            if isinstance(item, dict) and item.get("link")
        ]


def _position_to_score(item: dict[str, Any]) -> float | None:
    """Convert a result position to a descending score."""

    position = item.get("position")
    if not isinstance(position, int) or position <= 0:
        return None
    return 1 / position


def normalize_provider(value: str) -> str:
    """Normalize and validate a provider name."""

    provider = value.strip().lower()
    if provider in {"bing", "serper", "searxng"}:
        return provider
    raise AppError("不支持的联网搜索供应商，请使用 searxng、bing 或 serper。", code=4105)


def resolve_provider_endpoint(provider: str, configured_endpoint: str) -> str:
    """Resolve the effective provider endpoint."""

    normalized = normalize_provider(provider)
    return configured_endpoint.strip() or DEFAULT_ENDPOINTS.get(normalized, "")


def _raise_for_provider_status(response: httpx.Response, provider: str) -> None:
    """Raise a search-specific error with actionable diagnostics."""

    if response.is_success:
        return

    preview = response.text[:300]
    status_code = response.status_code
    if status_code in {401, 403}:
        message = (
            f"{provider} 联网搜索认证失败或权限不足，请检查 API Key、账号状态、额度，以及服务是否限制当前网络。"
        )
    elif status_code == 429:
        message = f"{provider} 联网搜索请求过于频繁或额度已用尽，请稍后重试或检查套餐额度。"
    elif 500 <= status_code < 600:
        message = f"{provider} 联网搜索服务暂时不可用，请稍后重试。"
    else:
        message = f"{provider} 联网搜索返回异常状态码 {status_code}。"
    raise WebSearchProviderError(
        message=message,
        provider=provider,
        provider_status_code=status_code,
        response_preview=preview,
    )
