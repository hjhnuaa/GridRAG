"""Web search endpoints."""

from __future__ import annotations

import httpx
from fastapi import APIRouter

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.common import ApiResponse, success_response
from app.schemas.web_search import WebSearchRequest, WebSearchResponse, WebSearchStatusResponse
from app.services.web_search import (
    WebSearchProviderError,
    WebSearchService,
    normalize_provider,
    resolve_provider_endpoint,
)

router = APIRouter(prefix="/web-search", tags=["联网搜索"])
logger = get_logger(__name__)


@router.post("")
async def search_web(payload: WebSearchRequest) -> ApiResponse[WebSearchResponse]:
    """Run a configured web search."""

    try:
        items = await WebSearchService().search(payload.query, payload.max_results)
    except WebSearchProviderError as exc:
        logger.warning(
            "web_search_provider_failed",
            provider=exc.provider,
            status_code=exc.provider_status_code,
            response=exc.response_preview,
        )
        raise exc
    except httpx.HTTPError as exc:
        logger.exception("web_search_failed", error=str(exc))
        raise AppError("联网搜索失败，请检查搜索服务配置。", code=4104) from exc
    return success_response(WebSearchResponse(items=items))


@router.get("/status")
async def web_search_status(probe: bool = False) -> ApiResponse[WebSearchStatusResponse]:
    """Return safe diagnostics for the configured web search provider."""

    settings = get_settings()
    try:
        provider = normalize_provider(settings.web_search_provider)
        endpoint = resolve_provider_endpoint(provider, settings.web_search_endpoint)
    except AppError as exc:
        return success_response(
            WebSearchStatusResponse(
                enabled=settings.web_search_enabled,
                provider=settings.web_search_provider,
                endpoint=settings.web_search_endpoint,
                api_key_configured=bool(settings.web_search_api_key),
                ok=False,
                message=exc.message,
            )
        )

    if not settings.web_search_enabled:
        return success_response(
            WebSearchStatusResponse(
                enabled=False,
                provider=provider,
                endpoint=endpoint,
                api_key_configured=bool(settings.web_search_api_key),
                ok=False,
                message="联网搜索已关闭，请设置 WEB_SEARCH_ENABLED=true。",
            )
        )

    if provider in {"bing", "serper"} and not settings.web_search_api_key:
        return success_response(
            WebSearchStatusResponse(
                enabled=True,
                provider=provider,
                endpoint=endpoint,
                api_key_configured=False,
                ok=False,
                message="当前供应商需要 API Key，请配置 WEB_SEARCH_API_KEY。",
            )
        )

    if provider == "searxng" and not settings.web_search_endpoint:
        return success_response(
            WebSearchStatusResponse(
                enabled=True,
                provider=provider,
                endpoint=endpoint,
                api_key_configured=False,
                ok=False,
                message="SearXNG 需要配置 WEB_SEARCH_ENDPOINT。",
            )
        )

    if not probe:
        return success_response(
            WebSearchStatusResponse(
                enabled=True,
                provider=provider,
                endpoint=endpoint,
                api_key_configured=bool(settings.web_search_api_key),
                ok=True,
                message="联网搜索配置已启用。添加 probe=true 可执行一次真实连通性测试。",
            )
        )

    try:
        items = await WebSearchService().search("test", 1)
    except WebSearchProviderError as exc:
        return success_response(
            WebSearchStatusResponse(
                enabled=True,
                provider=provider,
                endpoint=endpoint,
                api_key_configured=bool(settings.web_search_api_key),
                ok=False,
                message=exc.message,
                provider_status_code=exc.provider_status_code,
                response_preview=exc.response_preview,
            )
        )
    except httpx.HTTPError as exc:
        return success_response(
            WebSearchStatusResponse(
                enabled=True,
                provider=provider,
                endpoint=endpoint,
                api_key_configured=bool(settings.web_search_api_key),
                ok=False,
                message=f"联网搜索连接失败：{exc}",
            )
        )

    return success_response(
        WebSearchStatusResponse(
            enabled=True,
            provider=provider,
            endpoint=endpoint,
            api_key_configured=bool(settings.web_search_api_key),
            ok=True,
            message="联网搜索连通性测试成功。",
            sample_count=len(items),
        )
    )
