"""Run reproducible RAG retrieval, rerank, performance, and ingest evaluations."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import shutil
import sys
import tempfile
import time
import warnings
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import chromadb
from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.ingest.embedder import EmbeddingService
from app.ingest.loader import DocumentParser
from app.rag.chunker import DocumentChunker
from app.rag.reranker import BGEReranker
from app.rag.types import Chunk, ChunkMetadata

K_VALUES = (1, 3, 5, 10)
RERANK_K_VALUES = (1, 3, 5)
README_START = "<!-- RAG_EVAL_RESULTS_START -->"
README_END = "<!-- RAG_EVAL_RESULTS_END -->"


@dataclass(frozen=True, slots=True)
class EvalCase:
    """One deterministic evaluation question."""

    question: str
    doc_type: str
    expected_doc_title: str
    expected_keywords: list[str]


@dataclass(frozen=True, slots=True)
class ManifestItem:
    """One knowledge document listed in the demo manifest."""

    doc_type: str
    relative_path: str
    title: str

    @property
    def doc_id(self) -> str:
        """Return a stable document id for evaluation metadata."""

        return Path(self.relative_path).stem


@dataclass(slots=True)
class QueryTimings:
    """Per-query timing data in milliseconds."""

    dense_ms: float
    sparse_ms: float
    fusion_ms: float
    rerank_ms: float
    e2e_ms: float


class EvalChromaStore:
    """Temporary Chroma store used only by the evaluation script."""

    def __init__(self, persist_dir: Path, collection_prefix: str) -> None:
        """Initialize an isolated Chroma client."""

        self.persist_dir = persist_dir
        self.collection_prefix = collection_prefix
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.chunk_counts: defaultdict[str, int] = defaultdict(int)

    def collection_name(self, doc_type: str) -> str:
        """Build a Chroma collection name for the eval run."""

        return f"{self.collection_prefix}_eval_{doc_type}"

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Upsert chunks into per-doc-type collections."""

        grouped: dict[str, dict[str, list[Any]]] = {}
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            payload = grouped.setdefault(
                chunk.metadata.doc_type,
                {"ids": [], "documents": [], "metadatas": [], "embeddings": []},
            )
            payload["ids"].append(chunk.id)
            payload["documents"].append(chunk.text)
            payload["metadatas"].append(_chroma_metadata(chunk.metadata))
            payload["embeddings"].append(embedding)

        for doc_type, payload in grouped.items():
            collection = self.client.get_or_create_collection(
                name=self.collection_name(doc_type),
                metadata={"hnsw:space": "cosine"},
            )
            collection.upsert(
                ids=payload["ids"],
                documents=payload["documents"],
                metadatas=payload["metadatas"],
                embeddings=payload["embeddings"],
            )
            self.chunk_counts[doc_type] += len(payload["ids"])

    def query(self, doc_type: str, embedding: list[float], top_k: int) -> list[Chunk]:
        """Query one doc-type collection."""

        collection = self.client.get_or_create_collection(
            name=self.collection_name(doc_type),
            metadata={"hnsw:space": "cosine"},
        )
        available = self.chunk_counts.get(doc_type, 0)
        if available <= 0:
            return []

        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, available),
            include=["documents", "metadatas", "distances"],
        )
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        chunks: list[Chunk] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances, strict=False):
            chunks.append(
                Chunk(
                    id=str(chunk_id),
                    text=str(text),
                    metadata=_metadata_from_chroma(metadata),
                    dense_score=max(0.0, 1.0 - float(distance or 0)),
                )
            )
        return chunks

    def close(self) -> None:
        """Release Chroma resources so the temporary index can be removed on Windows."""

        if hasattr(self.client, "close"):
            self.client.close()
            return
        system = getattr(self.client, "_system", None)
        if system is not None and hasattr(system, "stop"):
            system.stop()


class EvalBM25Index:
    """In-memory BM25 index over the deterministic eval corpus."""

    def __init__(self, chunks: list[Chunk]) -> None:
        """Build one BM25 model per document type."""

        self.by_doc_type: dict[str, list[Chunk]] = defaultdict(list)
        for chunk in chunks:
            self.by_doc_type[chunk.metadata.doc_type].append(chunk)

        self.models: dict[str, BM25Okapi] = {}
        for doc_type, doc_chunks in self.by_doc_type.items():
            self.models[doc_type] = BM25Okapi([tokenize(chunk.text) for chunk in doc_chunks])

    def search(self, query: str, doc_type: str, top_k: int) -> list[Chunk]:
        """Return sparse retrieval candidates."""

        chunks = self.by_doc_type.get(doc_type, [])
        model = self.models.get(doc_type)
        if not chunks or model is None:
            return []

        scores = model.get_scores(tokenize(query))
        ranked = sorted(zip(chunks, scores, strict=True), key=lambda item: float(item[1]), reverse=True)[:top_k]
        top_score = float(ranked[0][1]) if ranked else 0.0
        candidates: list[Chunk] = []
        for chunk, score in ranked:
            candidates.append(clone_chunk(chunk, sparse_score=0.0 if top_score <= 0 else float(score) / top_score))
        return candidates


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=PROJECT_ROOT / "data/eval/rag_eval_cases.jsonl")
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT / "data/knowledge_manifest.csv")
    parser.add_argument("--knowledge-root", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--output-json", type=Path, default=PROJECT_ROOT / "docs/evaluation/rag_eval_results.json")
    parser.add_argument("--output-md", type=Path, default=PROJECT_ROOT / "docs/evaluation/rag_eval_results.md")
    parser.add_argument("--readme", type=Path, default=None, help="Optional README path to update in place.")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--keep-temp-index", action="store_true")
    return parser.parse_args()


async def run_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    """Run the full deterministic evaluation."""

    settings = get_settings()
    top_k = args.top_k or settings.rag_retrieval_top_k
    cases = load_cases(args.cases)
    manifest = load_manifest(args.manifest)
    temp_root = Path(tempfile.mkdtemp(prefix="gridrag_eval_chroma_"))
    started_at = time.perf_counter()
    store: EvalChromaStore | None = None

    try:
        parser = DocumentParser()
        chunker = DocumentChunker()
        embedder = EmbeddingService()
        store = EvalChromaStore(temp_root, settings.chroma_collection_prefix)
        ingest_report, chunks = await build_eval_index(
            manifest=manifest,
            knowledge_root=args.knowledge_root,
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            store=store,
        )
        bm25_index = EvalBM25Index(chunks)
        reranker = BGEReranker()
        query_results, timings = await evaluate_queries(
            cases=cases,
            store=store,
            bm25_index=bm25_index,
            embedder=embedder,
            reranker=reranker,
            top_k=top_k,
        )
        report = build_report(
            status="success",
            cases=cases,
            manifest=manifest,
            ingest_report=ingest_report,
            query_results=query_results,
            timings=timings,
            top_k=top_k,
            temp_root=temp_root,
            total_eval_ms=(time.perf_counter() - started_at) * 1000,
            error=None,
        )
    except Exception as exc:
        report = build_report(
            status="failed",
            cases=load_cases(args.cases) if args.cases.exists() else [],
            manifest=load_manifest(args.manifest) if args.manifest.exists() else [],
            ingest_report={"successful_documents": 0, "failed_documents": [], "total_chunks": 0},
            query_results=[],
            timings=[],
            top_k=top_k,
            temp_root=temp_root,
            total_eval_ms=(time.perf_counter() - started_at) * 1000,
            error=str(exc),
        )
    finally:
        if store is not None:
            store.close()
        import gc

        gc.collect()
        if not args.keep_temp_index:
            shutil.rmtree(temp_root, ignore_errors=True)

    write_report(args.output_json, args.output_md, report)
    if args.readme is not None:
        update_readme(args.readme, render_markdown(report, heading_level=2))
    if report["status"] != "success":
        raise RuntimeError(str(report.get("error") or "RAG evaluation failed"))
    return report


async def build_eval_index(
    manifest: list[ManifestItem],
    knowledge_root: Path,
    parser: DocumentParser,
    chunker: DocumentChunker,
    embedder: EmbeddingService,
    store: EvalChromaStore,
) -> tuple[dict[str, Any], list[Chunk]]:
    """Parse, chunk, embed, and index all manifest documents."""

    all_chunks: list[Chunk] = []
    failed_documents: list[dict[str, str]] = []
    doc_timings: list[float] = []
    doc_summaries: list[dict[str, Any]] = []
    started_at = time.perf_counter()

    for item in manifest:
        doc_started_at = time.perf_counter()
        file_path = knowledge_root / item.relative_path
        try:
            parsed = parser.parse(item.doc_id, file_path, item.title, item.doc_type)
            chunks = chunker.chunk(parsed)
            if not chunks:
                raise ValueError("文档未解析到可评估文本。")
            embeddings = await embedder.embed_texts([chunk.text for chunk in chunks])
            store.upsert_chunks(chunks, embeddings)
            elapsed_ms = (time.perf_counter() - doc_started_at) * 1000
            doc_timings.append(elapsed_ms)
            doc_summaries.append(
                {
                    "title": item.title,
                    "doc_type": item.doc_type,
                    "chunks": len(chunks),
                    "ingest_ms": round(elapsed_ms, 2),
                }
            )
            all_chunks.extend(chunks)
        except Exception as exc:
            failed_documents.append({"title": item.title, "path": item.relative_path, "error": str(exc)})

    successful_documents = len(manifest) - len(failed_documents)
    total_ms = (time.perf_counter() - started_at) * 1000
    return (
        {
            "total_documents": len(manifest),
            "successful_documents": successful_documents,
            "success_rate": ratio(successful_documents, len(manifest)),
            "failed_documents": failed_documents,
            "total_chunks": len(all_chunks),
            "average_chunks_per_document": ratio(len(all_chunks), successful_documents),
            "total_ingest_ms": round(total_ms, 2),
            "document_ingest_ms": summarize_values(doc_timings),
            "documents": doc_summaries,
        },
        all_chunks,
    )


async def evaluate_queries(
    cases: list[EvalCase],
    store: EvalChromaStore,
    bm25_index: EvalBM25Index,
    embedder: EmbeddingService,
    reranker: BGEReranker,
    top_k: int,
) -> tuple[list[dict[str, Any]], list[QueryTimings]]:
    """Evaluate retrieval and reranking for every case."""

    query_results: list[dict[str, Any]] = []
    timings: list[QueryTimings] = []

    for case in cases:
        query_started_at = time.perf_counter()

        dense_started_at = time.perf_counter()
        query_embedding = await embedder.embed_query(case.question)
        dense = store.query(case.doc_type, query_embedding, top_k)
        dense_ms = (time.perf_counter() - dense_started_at) * 1000

        sparse_started_at = time.perf_counter()
        sparse = bm25_index.search(case.question, case.doc_type, top_k)
        sparse_ms = (time.perf_counter() - sparse_started_at) * 1000

        fusion_started_at = time.perf_counter()
        fused = rrf_merge(dense, sparse)[:top_k]
        fusion_ms = (time.perf_counter() - fusion_started_at) * 1000

        rerank_started_at = time.perf_counter()
        reranked = await reranker.rerank(case.question, fused, top_n=max(RERANK_K_VALUES))
        rerank_ms = (time.perf_counter() - rerank_started_at) * 1000

        e2e_ms = (time.perf_counter() - query_started_at) * 1000
        timings.append(QueryTimings(dense_ms, sparse_ms, fusion_ms, rerank_ms, e2e_ms))
        query_results.append(
            {
                "question": case.question,
                "doc_type": case.doc_type,
                "expected_doc_title": case.expected_doc_title,
                "dense_rank": first_hit_rank(dense, case.expected_doc_title),
                "sparse_rank": first_hit_rank(sparse, case.expected_doc_title),
                "fused_rank": first_hit_rank(fused, case.expected_doc_title),
                "reranked_rank": first_hit_rank(reranked, case.expected_doc_title),
                "top_rerank_score": max((chunk.rerank_score or 0.0 for chunk in reranked), default=0.0),
                "dense_top_docs": top_doc_names(dense),
                "sparse_top_docs": top_doc_names(sparse),
                "fused_top_docs": top_doc_names(fused),
                "reranked_top_docs": top_doc_names(reranked),
                "timings_ms": {
                    "dense": round(dense_ms, 2),
                    "sparse": round(sparse_ms, 2),
                    "fusion": round(fusion_ms, 2),
                    "rerank": round(rerank_ms, 2),
                    "e2e": round(e2e_ms, 2),
                },
            }
        )
    return query_results, timings


def build_report(
    *,
    status: str,
    cases: list[EvalCase],
    manifest: list[ManifestItem],
    ingest_report: dict[str, Any],
    query_results: list[dict[str, Any]],
    timings: list[QueryTimings],
    top_k: int,
    temp_root: Path,
    total_eval_ms: float,
    error: str | None,
) -> dict[str, Any]:
    """Build a structured report."""

    settings = get_settings()
    return {
        "status": status,
        "error": error,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "manifest_documents": len(manifest),
            "eval_cases": len(cases),
            "source": "data/knowledge_manifest.csv + data/knowledge + data/eval/rag_eval_cases.jsonl",
        },
        "models": {
            "embedding_model": settings.embedding_model,
            "embedding_device": settings.embedding_device,
            "reranker_model": settings.reranker_model,
            "rag_retrieval_top_k": top_k,
            "rag_rerank_top_n": max(RERANK_K_VALUES),
            "rag_min_relevance_score": settings.rag_min_relevance_score,
        },
        "ingest": ingest_report,
        "retrieval": {
            "dense": ranking_summary([result["dense_rank"] for result in query_results], K_VALUES),
            "sparse": ranking_summary([result["sparse_rank"] for result in query_results], K_VALUES),
            "fused": ranking_summary([result["fused_rank"] for result in query_results], K_VALUES),
        },
        "rerank": {
            **ranking_summary([result["reranked_rank"] for result in query_results], RERANK_K_VALUES),
            "grounded_rate": ratio(
                sum(result["top_rerank_score"] >= settings.rag_min_relevance_score for result in query_results),
                len(query_results),
            ),
            "average_top_rerank_score": round(
                ratio(sum(result["top_rerank_score"] for result in query_results), len(query_results)),
                4,
            ),
        },
        "performance": performance_summary(timings),
        "query_results": query_results,
        "notes": [
            "本评估不调用大模型生成答案，只覆盖 RAG 检索、排序、重排、性能和入库链路。",
            "评估索引使用临时 Chroma 目录构建，运行结束后删除，不污染 storage/chroma。",
            f"临时索引目录: {temp_root}",
        ],
        "total_eval_ms": round(total_eval_ms, 2),
    }


def load_cases(path: Path) -> list[EvalCase]:
    """Load JSONL eval cases."""

    cases: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            cases.append(
                EvalCase(
                    question=str(payload["question"]),
                    doc_type=str(payload["doc_type"]),
                    expected_doc_title=str(payload["expected_doc_title"]),
                    expected_keywords=[str(item) for item in payload.get("expected_keywords", [])],
                )
            )
    return cases


def load_manifest(path: Path) -> list[ManifestItem]:
    """Load the demo knowledge manifest."""

    items: list[ManifestItem] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            items.append(
                ManifestItem(
                    doc_type=str(row["doc_type"]),
                    relative_path=str(row["relative_path"]),
                    title=str(row["title"]),
                )
            )
    return items


def tokenize(text: str) -> list[str]:
    """Tokenize Chinese text for BM25."""

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pkg_resources is deprecated as an API.*",
            category=UserWarning,
        )
        import jieba

    return [token.strip() for token in jieba.lcut_for_search(text) if token.strip()]


def rrf_merge(dense: list[Chunk], sparse: list[Chunk], k: int = 60) -> list[Chunk]:
    """Fuse dense and sparse rankings with reciprocal rank fusion."""

    merged: dict[str, Chunk] = {}
    scores: defaultdict[str, float] = defaultdict(float)
    for rank, chunk in enumerate(dense, start=1):
        merged.setdefault(chunk.id, clone_chunk(chunk))
        scores[chunk.id] += 1 / (k + rank)
    for rank, chunk in enumerate(sparse, start=1):
        if chunk.id in merged:
            merged[chunk.id].sparse_score = chunk.sparse_score
        else:
            merged[chunk.id] = clone_chunk(chunk)
        scores[chunk.id] += 1 / (k + rank)
    fused = list(merged.values())
    for chunk in fused:
        chunk.fused_score = scores[chunk.id]
    return sorted(fused, key=lambda item: item.fused_score or 0, reverse=True)


def clone_chunk(
    chunk: Chunk,
    *,
    dense_score: float | None = None,
    sparse_score: float | None = None,
    fused_score: float | None = None,
    rerank_score: float | None = None,
) -> Chunk:
    """Copy a chunk while optionally overriding scores."""

    return Chunk(
        id=chunk.id,
        text=chunk.text,
        metadata=chunk.metadata,
        dense_score=chunk.dense_score if dense_score is None else dense_score,
        sparse_score=chunk.sparse_score if sparse_score is None else sparse_score,
        fused_score=chunk.fused_score if fused_score is None else fused_score,
        rerank_score=chunk.rerank_score if rerank_score is None else rerank_score,
    )


def first_hit_rank(chunks: list[Chunk], expected_doc_title: str) -> int | None:
    """Return the 1-based rank of the first chunk from the expected document."""

    for index, chunk in enumerate(chunks, start=1):
        if chunk.metadata.doc_name == expected_doc_title:
            return index
    return None


def top_doc_names(chunks: list[Chunk], limit: int = 5) -> list[str]:
    """Return top unique document names."""

    names: list[str] = []
    for chunk in chunks:
        if chunk.metadata.doc_name not in names:
            names.append(chunk.metadata.doc_name)
        if len(names) >= limit:
            break
    return names


def ranking_summary(ranks: list[int | None], k_values: tuple[int, ...]) -> dict[str, Any]:
    """Return Recall@K, MRR, and nDCG@K for document-level binary relevance."""

    total = len(ranks)
    summary: dict[str, Any] = {"mrr": round(ratio(sum(1 / rank for rank in ranks if rank), total), 4)}
    for k_value in k_values:
        summary[f"recall_at_{k_value}"] = ratio(sum(rank is not None and rank <= k_value for rank in ranks), total)
        summary[f"ndcg_at_{k_value}"] = round(
            ratio(sum(1 / math.log2(rank + 1) for rank in ranks if rank is not None and rank <= k_value), total),
            4,
        )
    return summary


def performance_summary(timings: list[QueryTimings]) -> dict[str, dict[str, float]]:
    """Summarize per-query timing data."""

    return {
        "dense_ms": summarize_values([item.dense_ms for item in timings]),
        "sparse_ms": summarize_values([item.sparse_ms for item in timings]),
        "fusion_ms": summarize_values([item.fusion_ms for item in timings]),
        "rerank_ms": summarize_values([item.rerank_ms for item in timings]),
        "e2e_ms": summarize_values([item.e2e_ms for item in timings]),
    }


def summarize_values(values: list[float]) -> dict[str, float]:
    """Return average, p50, and p95 for a numeric list."""

    if not values:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0}
    return {
        "avg": round(sum(values) / len(values), 2),
        "p50": round(percentile(values, 50), 2),
        "p95": round(percentile(values, 95), 2),
    }


def percentile(values: list[float], percent: float) -> float:
    """Compute a nearest-rank percentile with linear interpolation."""

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percent / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def ratio(numerator: float, denominator: float) -> float:
    """Return a rounded ratio, guarding empty denominators."""

    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _chroma_metadata(metadata: ChunkMetadata) -> dict[str, str | int]:
    """Return Chroma-compatible metadata without null values."""

    payload = metadata.to_dict()
    return {key: value for key, value in payload.items() if value is not None}


def _metadata_from_chroma(metadata: dict[str, Any]) -> ChunkMetadata:
    """Convert Chroma metadata into ChunkMetadata."""

    return ChunkMetadata(
        doc_id=str(metadata.get("doc_id", "")),
        doc_name=str(metadata.get("doc_name", "")),
        doc_type=str(metadata.get("doc_type", "")),
        page=int(metadata["page"]) if metadata.get("page") is not None else None,
        section=str(metadata["section"]) if metadata.get("section") else None,
        created_at=str(metadata.get("created_at", "")),
        chunk_index=int(metadata.get("chunk_index", 0)),
    )


def write_report(output_json: Path, output_md: Path, report: dict[str, Any]) -> None:
    """Write JSON and Markdown reports."""

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(render_markdown(report, heading_level=1), encoding="utf-8")


def render_markdown(report: dict[str, Any], heading_level: int) -> str:
    """Render the report as Markdown."""

    heading = "#" * heading_level
    if report["status"] != "success":
        return (
            f"{heading} 评估结果\n\n"
            f"- 状态：失败\n"
            f"- 生成时间：`{report['generated_at']}`\n"
            f"- 失败原因：{report.get('error') or '未知错误'}\n"
        )

    retrieval = report["retrieval"]
    rerank = report["rerank"]
    ingest = report["ingest"]
    performance = report["performance"]
    lines = [
        f"{heading} 评估结果",
        "",
        f"- 生成时间：`{report['generated_at']}`",
        f"- 数据集：{report['dataset']['manifest_documents']} 份知识文档，{report['dataset']['eval_cases']} 条问题",
        f"- 模型：Embedding `{report['models']['embedding_model']}`；Reranker `{report['models']['reranker_model']}`",
        "- 范围：不包含大模型生成质量评估，只覆盖 RAG 检索、排序、重排、性能和入库链路。",
        "",
        "### 指标总览",
        "",
        "| 类别 | 指标 | 结果 |",
        "| --- | --- | ---: |",
        f"| 入库能力 | 文档成功率 | {fmt_pct(ingest['success_rate'])} |",
        f"| 入库能力 | 总分块数 | {ingest['total_chunks']} |",
        f"| 检索质量 | 融合 Recall@5 | {fmt_pct(retrieval['fused']['recall_at_5'])} |",
        f"| 检索排序 | 融合 MRR | {retrieval['fused']['mrr']:.4f} |",
        f"| 检索排序 | 融合 nDCG@5 | {retrieval['fused']['ndcg_at_5']:.4f} |",
        f"| 重排质量 | Rerank Recall@5 | {fmt_pct(rerank['recall_at_5'])} |",
        f"| 重排质量 | Grounded rate | {fmt_pct(rerank['grounded_rate'])} |",
        f"| 性能 | 端到端检索 p95 | {performance['e2e_ms']['p95']:.2f} ms |",
        "",
        "### 检索与排序",
        "",
        "| 通道 | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | nDCG@5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, key in (("向量", "dense"), ("关键词", "sparse"), ("融合", "fused")):
        item = retrieval[key]
        lines.append(
            "| "
            f"{label} | {fmt_pct(item['recall_at_1'])} | {fmt_pct(item['recall_at_3'])} | "
            f"{fmt_pct(item['recall_at_5'])} | {fmt_pct(item['recall_at_10'])} | "
            f"{item['mrr']:.4f} | {item['ndcg_at_5']:.4f} |"
        )
    lines.extend(
        [
            "",
            "### 重排质量",
            "",
            "| Recall@1 | Recall@3 | Recall@5 | MRR | Grounded rate | Top score 均值 |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
            "| "
            f"{fmt_pct(rerank['recall_at_1'])} | {fmt_pct(rerank['recall_at_3'])} | "
            f"{fmt_pct(rerank['recall_at_5'])} | {rerank['mrr']:.4f} | "
            f"{fmt_pct(rerank['grounded_rate'])} | {rerank['average_top_rerank_score']:.4f} |",
            "",
            "### 性能",
            "",
            "| 阶段 | Avg | P50 | P95 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for label, key in (
        ("向量检索", "dense_ms"),
        ("关键词检索", "sparse_ms"),
        ("融合", "fusion_ms"),
        ("重排", "rerank_ms"),
        ("端到端检索", "e2e_ms"),
    ):
        item = performance[key]
        lines.append(f"| {label} | {item['avg']:.2f} ms | {item['p50']:.2f} ms | {item['p95']:.2f} ms |")
    lines.extend(
        [
            "",
            "### 入库能力",
            "",
            "| 指标 | 结果 |",
            "| --- | ---: |",
            f"| 文档总数 | {ingest['total_documents']} |",
            f"| 成功文档数 | {ingest['successful_documents']} |",
            f"| 失败文档数 | {len(ingest['failed_documents'])} |",
            f"| 总分块数 | {ingest['total_chunks']} |",
            f"| 平均分块数 / 文档 | {ingest['average_chunks_per_document']:.2f} |",
            f"| 总入库耗时 | {ingest['total_ingest_ms']:.2f} ms |",
            f"| 单文档入库 P95 | {ingest['document_ingest_ms']['p95']:.2f} ms |",
            "",
            "### 结论",
            "",
            build_conclusion(report),
            "",
        ]
    )
    return "\n".join(lines)


def build_conclusion(report: dict[str, Any]) -> str:
    """Build a concise conclusion from headline metrics."""

    fused_recall = report["retrieval"]["fused"]["recall_at_5"]
    rerank_recall = report["rerank"]["recall_at_5"]
    ingest_success = report["ingest"]["success_rate"]
    if min(fused_recall, rerank_recall, ingest_success) >= 0.9:
        return "固定演示集上，入库、融合检索和重排链路表现稳定，可作为项目展示和后续调参基线。"
    return "固定演示集上已形成可复现评估基线，后续可优先优化低命中问题对应的分块、查询改写或重排阈值。"


def fmt_pct(value: float) -> str:
    """Format a ratio as a percentage."""

    return f"{value * 100:.1f}%"


def update_readme(readme_path: Path, section_md: str) -> None:
    """Insert or replace the README evaluation section."""

    content = readme_path.read_text(encoding="utf-8")
    block = f"{README_START}\n{section_md.strip()}\n{README_END}"
    if README_START in content and README_END in content:
        before, rest = content.split(README_START, 1)
        _, after = rest.split(README_END, 1)
        updated = f"{before}{block}{after}"
    else:
        marker = "\n## 面试准备文档"
        if marker in content:
            updated = content.replace(marker, f"\n{block}\n{marker}", 1)
        else:
            updated = f"{content.rstrip()}\n\n{block}\n"
    readme_path.write_text(updated, encoding="utf-8")


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(run_evaluation(args))


if __name__ == "__main__":
    main()
