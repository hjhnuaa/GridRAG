"""Embedding model wrapper."""

from __future__ import annotations

import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Asynchronous wrapper around a local SentenceTransformer embedding model."""

    def __init__(self) -> None:
        """Initialize the embedding model lazily."""

        self.settings = get_settings()
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Return the local embedding model."""

        if self._model is None:
            logger.info(
                "loading_embedding_model",
                model=self.settings.embedding_model,
                device=self.settings.embedding_device,
            )
            self._model = SentenceTransformer(
                self.settings.embedding_model,
                device=self.settings.embedding_device,
            )
        return self._model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts asynchronously."""

        if not texts:
            return []
        return await asyncio.to_thread(self._embed_sync, texts)

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""

        embeddings = await self.embed_texts([query])
        return embeddings[0]

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Run synchronous embedding generation."""

        model = self._get_model()
        vectors = model.encode(
            texts,
            batch_size=self.settings.embedding_batch_size,
            normalize_embeddings=self.settings.embedding_normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Return the singleton embedding service."""

    return EmbeddingService()

