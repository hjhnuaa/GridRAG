"""Tests for prompt rendering contracts."""

from __future__ import annotations

from app.rag.generator import PromptRenderer
from app.rag.types import Chunk, ChunkMetadata


def _chunk(text: str = "申请低保需提交身份证明。") -> Chunk:
    return Chunk(
        id="chunk-1",
        text=text,
        metadata=ChunkMetadata(
            doc_id="doc-1",
            doc_name="低保政策",
            doc_type="policy",
            page=2,
            section="申请材料",
            created_at="2026-01-01T00:00:00+00:00",
            chunk_index=1,
        ),
    )


def test_qa_prompt_renders_grounding_and_citation_rules() -> None:
    """QA prompt should preserve evidence priority and citation rules."""

    prompt = PromptRenderer().render(
        "qa_system.j2",
        contexts=[_chunk()],
        memories=["个人偏好：用户负责朝阳社区。"],
        web_results=[],
        question="低保需要什么材料？",
    )

    assert "本地知识库参考资料是正式依据" in prompt
    assert "规则与记忆上下文只能作为回答风格" in prompt
    assert "组织规则 < 项目规则 < 个人偏好 < 本地规则 < 全局记忆 < 自动经验 < 会话记忆" in prompt
    assert "每个关键事实、条件、流程、时限或建议句末必须标注来源编号" in prompt
    assert "类型：policy" in prompt
    assert "低保需要什么材料？" in prompt


def test_event_assist_prompt_declares_strict_json_and_priority_rules() -> None:
    """Event assist prompt should constrain category, priority, and JSON output."""

    prompt = PromptRenderer().render(
        "event_assist.j2",
        description="楼道电线裸露，居民担心起火。",
        contexts=[_chunk("楼道安全隐患应先核实现场并及时上报。")],
    )

    assert "只输出一个合法 JSON 对象" in prompt
    assert "HAZARD：消防、燃气、电气" in prompt
    assert "5：涉及人员生命安全" in prompt
    assert '"suggested_category": "HAZARD"' in prompt


def test_visit_suggest_prompt_declares_privacy_and_action_rules() -> None:
    """Visit prompt should avoid sensitive data and require actionable suggestions."""

    prompt = PromptRenderer().render(
        "visit_suggest.j2",
        resident_json='{"id":"r1","tags":["ELDERLY_ALONE"],"phone":"13800000000"}',
        visits_json="[]",
        related_events_json="[]",
    )

    assert "不要输出居民身份证号、手机号等敏感信息" in prompt
    assert "建议必须是可执行动作" in prompt
    assert "resident_id 由系统补充，不要输出" in prompt
