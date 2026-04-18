"""Application configuration based on pydantic-settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "GridRAG"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    auth_disabled: bool = True
    secret_key: str = "replace-this-secret-key-with-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    database_url: str = "mysql+asyncmy://gridrag:gridrag@127.0.0.1:3306/gridrag"
    sync_database_url: str = "mysql+pymysql://gridrag:gridrag@127.0.0.1:3306/gridrag"
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_auto_create: bool = False

    redis_url: str = "redis://127.0.0.1:6379/0"
    cache_ttl_seconds: int = 1800

    qwen_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("QWEN_API_KEY", "OPENAI_API_KEY"),
    )
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    qwen_timeout_seconds: float = 60.0
    qwen_temperature: float = 0.2
    qwen_max_tokens: int = 1024

    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    embedding_normalize: bool = True
    embedding_fallback_model: str = ""

    reranker_model: str = "BAAI/bge-reranker-large"
    reranker_use_fp16: bool = False

    chroma_persist_dir: str = "storage/chroma"
    chroma_collection_prefix: str = "gridrag"
    chroma_result_k: int = 20

    rag_rewrite_query: bool = False
    rag_retrieval_top_k: int = 20
    rag_rerank_top_n: int = 5
    rag_min_relevance_score: float = 0.35
    rag_max_total_tokens: int = 4096

    celery_broker_url: str = "redis://127.0.0.1:6379/1"
    celery_result_backend: str = "redis://127.0.0.1:6379/2"
    celery_task_always_eager: bool = True

    storage_dir: str = "storage"
    upload_dir: str = "storage/uploads"
    log_dir: str = "logs"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> list[str] | Any:
        """Allow CORS origins to be provided as a comma-separated string."""

        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("qwen_api_key", mode="before")
    @classmethod
    def _fallback_openai_api_key(cls, value: Any) -> str:
        """Fall back to OPENAI_API_KEY when QWEN_API_KEY is blank."""

        if isinstance(value, str) and value.strip():
            return value
        return os.getenv("OPENAI_API_KEY", "").strip()

    @property
    def project_root(self) -> Path:
        """Return the repository root directory."""

        return Path(__file__).resolve().parents[3]

    @property
    def backend_root(self) -> Path:
        """Return the backend root directory."""

        return Path(__file__).resolve().parents[2]

    @property
    def prompt_dir(self) -> Path:
        """Return the prompts directory."""

        return self.backend_root / "prompts"

    @property
    def chroma_dir(self) -> Path:
        """Return the Chroma persistence directory."""

        return self.project_root / self.chroma_persist_dir

    @property
    def upload_path(self) -> Path:
        """Return the upload directory path."""

        return self.project_root / self.upload_dir

    @property
    def logs_path(self) -> Path:
        """Return the log directory path."""

        return self.project_root / self.log_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings instance."""

    return Settings()
