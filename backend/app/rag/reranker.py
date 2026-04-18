"""BGE reranker wrapper."""

from __future__ import annotations

import asyncio
import math
from functools import lru_cache
from typing import Protocol, cast

from sentence_transformers import CrossEncoder

from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.types import Chunk

logger = get_logger(__name__)


class _RerankerModel(Protocol):
    """Protocol implemented by supported reranker backends."""

    def compute_score(self, sentence_pairs: list[list[str]]) -> float | list[float]:
        """Return scores for sentence pairs."""


class _CrossEncoderAdapter:
    """Adapter that exposes a FlagEmbedding-like interface."""

    def __init__(self, model_name: str, device: str) -> None:
        """Initialize the fallback cross-encoder."""

        self.model = CrossEncoder(model_name, device=device, trust_remote_code=True)

    def compute_score(self, sentence_pairs: list[list[str]]) -> list[float]:
        """Predict scores with the cross-encoder."""

        scores = self.model.predict(sentence_pairs, show_progress_bar=False)
        return [float(score) for score in scores]


class BGEReranker:
    """Normalize and rank retrieval candidates using a local reranker model."""

    def __init__(self) -> None:
        """Initialize the reranker lazily."""

        self.settings = get_settings()
        self._model: _RerankerModel | None = None

    def _get_model(self) -> _RerankerModel:
        """Return the local reranker model."""

        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> _RerankerModel:
        """Load the preferred reranker backend with fallback support."""

        logger.info(
            "loading_reranker_model",
            model=self.settings.reranker_model,
            use_fp16=self.settings.reranker_use_fp16,
        )
        try:
            from FlagEmbedding import FlagReranker

            return cast(
                _RerankerModel,
                FlagReranker(
                    self.settings.reranker_model,
                    use_fp16=self.settings.reranker_use_fp16,
                ),
            )
        except Exception as exc:
            logger.warning(
                "flagembedding_unavailable_falling_back",
                error=str(exc),
                model=self.settings.reranker_model,
            )
            return _CrossEncoderAdapter(
                model_name=self.settings.reranker_model,
                device=self.settings.embedding_device,
            )

    async def rerank(self, query: str, candidates: list[Chunk], top_n: int | None = None) -> list[Chunk]:
        """Rerank retrieved candidates and return the top subset."""

        if not candidates:
            return []
        limit = top_n or self.settings.rag_rerank_top_n
        scores = await asyncio.to_thread(self._compute_scores, query, candidates)
        reranked: list[Chunk] = []
        for chunk, score in zip(candidates, scores, strict=True):
            chunk.rerank_score = score
            reranked.append(chunk)
        reranked.sort(key=lambda item: item.rerank_score or 0, reverse=True)
        return reranked[:limit]

    def _compute_scores(self, query: str, candidates: list[Chunk]) -> list[float]:
        """Compute normalized rerank scores."""

        model = self._get_model()
        pairs = [[query, chunk.text] for chunk in candidates]
        raw_scores = model.compute_score(pairs)
        if isinstance(raw_scores, float):
            raw_scores = [raw_scores]
        return [1 / (1 + math.exp(-float(score))) for score in raw_scores]


@lru_cache(maxsize=1)
def get_reranker() -> BGEReranker:
    """Return the singleton reranker."""

    return BGEReranker()
