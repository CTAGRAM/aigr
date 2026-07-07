"""Confidence scorer.

Confidence blends: source quality (how trustworthy the provider is), worker self-confidence, and
corroboration (multiple agreeing sources raise it). Kept simple and deterministic.

`merge_results` is retained as a backward-compatible entry point (merge + score in the original shape).
"""
from __future__ import annotations

from typing import Any

from .merger import merge
from .result import WorkerResult

_SOURCE_QUALITY = {
    "memory": 1.0,
    "github": 0.9,
    "tavily": 0.75,
    "company": 0.7,
    "conference": 0.6,
}


def score(results: list[WorkerResult]) -> float:
    useful = [
        r for r in results
        if isinstance(r, WorkerResult) and r.success and (r.data or r.confidence)
    ]
    if not useful:
        return 0.0
    weighted = [_SOURCE_QUALITY.get(r.provider, 0.5) * (r.confidence or 0.5) for r in useful]
    base = sum(weighted) / len(weighted)
    corroboration = 0.05 * (len(useful) - 1)          # agreeing sources raise confidence
    return round(min(1.0, base + corroboration), 2)


def merge_results(query: str, workers: list[Any]) -> dict:
    """Backward-compatible: merge + score in the pre-refactor return shape."""
    wrs = [w for w in workers if isinstance(w, WorkerResult)]
    merged = merge(query, wrs)
    return {
        "query": query,
        "confidence": score(wrs),
        "summary": merged["summary"],
        "sources": merged["sources"],
        "matches": merged["matches"],
    }
