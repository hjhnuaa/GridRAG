"""AI assistant services for event drafting and resident visits."""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.rag.generator import QwenGenerator, get_qwen_generator
from app.rag.reranker import BGEReranker, get_reranker
from app.rag.retriever import HybridRetriever
from app.schemas.event import EventAIAssistResponse
from app.schemas.resident import VisitSuggestResponse

logger = get_logger(__name__)

TAG_SUGGESTIONS: dict[str, tuple[str, ...]] = {
    "ELDERLY_ALONE": ("确认近期用药和送餐情况", "检查燃气照明与防跌倒风险"),
    "LOW_INCOME": ("核实近期收入变化和补助申领进度",),
    "DISABLED": ("确认辅具使用和上门代办需求",),
    "CHRONIC_DISEASE": ("核对慢病复诊安排和备药情况",),
    "LEFT_BEHIND_CHILD": ("了解监护陪伴和在校状态变化",),
}

TAG_RISK_LABELS: dict[str, str] = {
    "ELDERLY_ALONE": "独居生活保障",
    "LOW_INCOME": "家庭收入波动",
    "DISABLED": "无障碍与代办需求",
    "CHRONIC_DISEASE": "慢病复诊用药",
    "LEFT_BEHIND_CHILD": "监护陪伴情况",
}


def _append_unique(items: list[str], value: str) -> None:
    """Append a suggestion only once."""

    text = value.strip()
    if text and text not in items:
        items.append(text)


def _build_local_visit_suggest(
    resident: dict[str, object],
    visits: list[dict[str, object]],
    related_events: list[dict[str, object]],
) -> VisitSuggestResponse:
    """Build deterministic visit suggestions when the LLM is unavailable."""

    resident_id = str(resident.get("id", ""))
    raw_tags = resident.get("tags")
    tag_items = raw_tags if isinstance(raw_tags, (list, tuple, set)) else []
    tags = [str(item) for item in tag_items]
    suggestions: list[str] = []

    for tag in tags:
        for suggestion in TAG_SUGGESTIONS.get(tag, ()):
            _append_unique(suggestions, suggestion)

    unresolved_events = [
        event for event in related_events if str(event.get("status", "")).upper() not in {"RESOLVED", "CLOSED"}
    ]
    if unresolved_events:
        _append_unique(suggestions, "跟进未闭环事项处置进展")

    latest_visit = visits[0] if visits else None
    if latest_visit:
        _append_unique(suggestions, "回看上次走访问题是否已缓解")
    else:
        _append_unique(suggestions, "首次走访先核实家庭基础情况")

    _append_unique(suggestions, "核对紧急联系人和求助渠道是否畅通")

    fallback_pool = [
        "确认近期生活物资和邻里支持情况",
        "询问本周是否存在新的诉求或困难",
        "提醒常用政策办理材料提前备齐",
    ]
    for suggestion in fallback_pool:
        if len(suggestions) >= 5:
            break
        _append_unique(suggestions, suggestion)

    risk_points: list[str] = []
    for tag in tags:
        label = TAG_RISK_LABELS.get(tag)
        if label and label not in risk_points:
            risk_points.append(label)
    if unresolved_events:
        risk_points.append(f"{len(unresolved_events)}件事项待跟进")
    if latest_visit:
        risk_points.append("上次走访问题需复核")
    else:
        risk_points.append("基础信息待补全")

    summary = "本次重点关注" + "、".join(risk_points[:3]) + "。"
    if len(summary) > 60:
        summary = "本次重点核实家庭近况、服务需求和未闭环问题。"

    return VisitSuggestResponse(
        resident_id=resident_id,
        suggestions=suggestions[:5],
        risk_summary=summary,
    )


async def generate_event_assist(
    session: AsyncSession,
    description: str,
    retriever: HybridRetriever | None = None,
    reranker: BGEReranker | None = None,
    generator: QwenGenerator | None = None,
) -> EventAIAssistResponse:
    """Generate event form suggestions grounded in policy and manual chunks."""

    effective_retriever = retriever or HybridRetriever()
    effective_reranker = reranker or get_reranker()
    effective_generator = generator or get_qwen_generator()

    retrieval = await effective_retriever.retrieve(
        session=session,
        query=description,
        doc_types=["policy", "manual"],
        top_k=8,
    )
    contexts = await effective_reranker.rerank(description, retrieval.fused, top_n=3)
    payload = await effective_generator.generate_json(
        "event_assist.j2",
        description=description,
        contexts=contexts,
    )
    return EventAIAssistResponse.model_validate(payload)


async def generate_visit_suggest(
    resident: dict[str, object],
    visits: list[dict[str, object]],
    related_events: list[dict[str, object]],
    generator: QwenGenerator | None = None,
) -> VisitSuggestResponse:
    """Generate visit suggestions from resident profile data."""

    effective_generator = generator or get_qwen_generator()
    try:
        payload = await effective_generator.generate_json(
            "visit_suggest.j2",
            resident_json=json.dumps(resident, ensure_ascii=False, indent=2),
            visits_json=json.dumps(visits[:5], ensure_ascii=False, indent=2),
            related_events_json=json.dumps(related_events[:5], ensure_ascii=False, indent=2),
        )
        payload["resident_id"] = resident["id"]
        return VisitSuggestResponse.model_validate(payload)
    except AppError as exc:
        logger.warning(
            "visit_suggest_fallback",
            resident_id=str(resident.get("id", "")),
            code=exc.code,
            message=exc.message,
        )
        return _build_local_visit_suggest(resident, visits, related_events)
    except Exception as exc:
        logger.exception(
            "visit_suggest_unexpected_fallback",
            resident_id=str(resident.get("id", "")),
            error=str(exc),
        )
        return _build_local_visit_suggest(resident, visits, related_events)
