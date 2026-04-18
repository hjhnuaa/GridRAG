"""LangChain-backed Qwen generation and prompt rendering."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, cast

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptRenderer:
    """Render Jinja2 prompt templates from the prompts directory."""

    def __init__(self) -> None:
        """Initialize the Jinja2 environment."""

        settings = get_settings()
        self.environment = Environment(
            loader=FileSystemLoader(str(settings.prompt_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, template_name: str, **context: Any) -> str:
        """Render a prompt template."""

        template = self.environment.get_template(template_name)
        return template.render(**context)


class QwenGenerator:
    """Use LangChain chat models to render, stream, and parse Qwen responses."""

    def __init__(self, renderer: PromptRenderer | None = None) -> None:
        """Initialize the generator."""

        self.settings = get_settings()
        self.renderer = renderer or get_prompt_renderer()
        self.model = ChatOpenAI(
            model=self.settings.qwen_model,
            api_key=SecretStr(self.settings.qwen_api_key or "missing-key"),
            base_url=self.settings.qwen_base_url,
            temperature=self.settings.qwen_temperature,
            timeout=self.settings.qwen_timeout_seconds,
            model_kwargs={"max_tokens": self.settings.qwen_max_tokens},
        )
        self._text_chain = (
            ChatPromptTemplate.from_messages([("human", "{prompt}")])
            | self.model
            | StrOutputParser()
        )

    def render_prompt(self, template_name: str, **context: Any) -> str:
        """Render a prompt template."""

        return self.renderer.render(template_name, **context)

    async def stream_completion(self, prompt: str) -> Any:
        """Stream text chunks from a LangChain runnable."""

        self._ensure_api_key()
        async for chunk in self._text_chain.astream({"prompt": prompt}):
            yield str(chunk)

    async def generate_text(self, prompt: str) -> str:
        """Generate a non-streaming response."""

        self._ensure_api_key()
        return await self._text_chain.ainvoke({"prompt": prompt})

    async def generate_json(self, template_name: str, **context: Any) -> dict[str, Any]:
        """Render a template, call the model, and parse the first JSON object."""

        prompt = self.render_prompt(template_name, **context)
        text = await self.generate_text(prompt)
        try:
            return self._extract_json(text)
        except json.JSONDecodeError as exc:
            logger.exception("invalid_json_from_llm", response=text)
            raise AppError("AI 返回格式异常，请稍后重试。", code=5002) from exc

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract the first JSON object from model output."""

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match is None:
            raise json.JSONDecodeError("No JSON object found", text, 0)
        return cast(dict[str, Any], json.loads(match.group(0)))

    def _ensure_api_key(self) -> None:
        """Ensure the Qwen API key is configured."""

        if not self.settings.qwen_api_key:
            raise AppError("未配置 Qwen API Key，请设置 QWEN_API_KEY 或 OPENAI_API_KEY。", code=5003)


@lru_cache(maxsize=1)
def get_prompt_renderer() -> PromptRenderer:
    """Return the prompt renderer singleton."""

    return PromptRenderer()


@lru_cache(maxsize=1)
def get_qwen_generator() -> QwenGenerator:
    """Return the Qwen generator singleton."""

    return QwenGenerator()
