"""The engine: plan → execute → resolve → merge → score → summarize.

Knows nothing about worker implementations — only the planner (which workers), the registry (run them),
the resolver (canonical entity), the merger (assemble evidence), and the scorer (confidence). Swapping a
worker or storage backend never touches this file.

`lookup_person` is kept as a backward-compatible alias of `run`.
"""
from __future__ import annotations

import time

from . import registry
from .cache import entity_cache
from .graph import KnowledgeGraph
from .logging import get_logger
from .merger import merge
from .planner import plan
from .resolver import resolve
from .scorer import score

log = get_logger("engine")
_graph = KnowledgeGraph()


def _summary(person, merged: dict) -> str:
    if merged.get("summary"):
        return merged["summary"]
    bits: list[str] = []
    if person.name:
        bits.append(person.name)
    if person.company:
        bits.append(f"at {person.company}")
    if person.bio:
        bits.append(f"— {person.bio}")
    return " ".join(bits) or "No confident match found."


async def run(query: str) -> dict:
    key = query.strip().lower()
    if key in entity_cache:
        cached = dict(entity_cache[key])
        cached["cache_hit"] = True
        return cached

    start = time.perf_counter()
    names = plan(query)
    log.info("plan query=%r workers=%s", query, names)

    results = await registry.execute(names, query)      # list[WorkerResult]
    person = resolve(results)
    merged = merge(query, results)
    confidence = score(results)
    person.confidence = confidence

    related_entities: list[dict] = []
    relationships: list[dict] = []
    try:  # graph is best-effort — it must never fail the lookup
        _graph.update(person)
        related_entities = _graph.neighbors(person.id)
        relationships = _graph.relationships(person.id)
    except Exception as exc:  # noqa: BLE001
        log.warning("graph update failed: %s", exc)

    out = {
        "query": query,
        "person": person.to_dict(),
        "summary": _summary(person, merged),
        "confidence": confidence,
        "sources": merged["sources"],
        "matches": merged["matches"],
        "related_entities": related_entities,
        "relationships": relationships,
        "workers_used": [r.provider for r in results],
        "latency_ms": int((time.perf_counter() - start) * 1000),
        "cache_hit": False,
    }
    entity_cache[key] = out
    return out


# Backward-compatible name (older callers / the MCP layer).
lookup_person = run
