"""MCP server — the seam the orchestrator (Hermes / OpenClaw) plugs into.

Exposes the backend's memory + transcript + action tools over the Model Context Protocol, so the agent
brain can read what you saw/heard and file new tasks WITHOUT any custom glue. Both Hermes and OpenClaw
are MCP clients, so the same server works for either.

Requires: pip install mcp
Run:      python -m app.mcp_server   (stdio transport)
"""
from __future__ import annotations

import json
import os
import urllib.request

from .config import load_settings
from .memory.store import MemoryStore
from .osint.public_search import public_search
from .osint.engine import run as person_lookup

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - optional dependency
    raise SystemExit("MCP not installed. Run: pip install mcp") from exc

settings = load_settings()
memory = MemoryStore(settings.db_path)
mcp = FastMCP("aiglass")

# When Hermes writes a result, best-effort ping the API's /turn so it broadcasts on /ws/events and the
# glasses can speak it immediately. (Multi-process dev seam; production would use a shared Redis channel.)
_API_URL = os.getenv("AIGLASS_API_URL", "http://127.0.0.1:8000")


def _broadcast_result(text: str) -> None:
    try:
        payload = json.dumps({"role": "assistant", "text": text, "source": "hermes"}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if (tok := os.getenv("API_TOKEN")):
            headers["Authorization"] = f"Bearer {tok}"
        req = urllib.request.Request(
            _API_URL.rstrip("/") + "/turn", data=payload, headers=headers, method="POST",
        )
        urllib.request.urlopen(req, timeout=2.0).close()
    except Exception:
        pass  # never let a broadcast failure break the agent's write


@mcp.tool()
def search_memories(query: str, limit: int = 10) -> list[dict]:
    """Search the user's captured memories by keyword."""
    return [m.__dict__ for m in memory.search_memories(query, limit=limit)]


@mcp.tool()
def recent_transcripts(limit: int = 20) -> list[dict]:
    """Return the most recent conversation transcripts the glasses captured."""
    return [t.__dict__ for t in memory.recent_transcripts(limit=limit)]


@mcp.tool()
def list_action_items(limit: int = 50) -> list[dict]:
    """List open action items extracted from conversations."""
    return [m.__dict__ for m in memory.memories(kind="action_item", limit=limit)]


@mcp.tool()
def add_memory(kind: str, text: str) -> dict:
    """Let the agent write a fact/summary/result back into the user's memory (and sync it live)."""
    mid = memory.add_memory(kind, text, source="orchestrator")
    if kind in ("result", "reply", "answer"):
        _broadcast_result(text)   # surface finished work to the glasses in real time
    return {"id": mid, "kind": kind, "text": text}



@mcp.tool()
async def aiglass_public_search(
    query: str,
    max_results: int = 5,
) -> dict:
    """
    Search the public web.

    Use for:
    - People
    - Companies
    - Products
    - Technologies
    - Startups
    """

    return await public_search(
        query=query,
        max_results=max_results,
    )


@mcp.tool()
async def aiglass_person_lookup(query: str) -> dict:
    """
    Deep intelligence lookup on a person (also works for a company, product, or technology).

    Fans out to parallel OSINT workers (memory, web search, GitHub, ...), resolves them into one
    canonical entity, scores the evidence, and returns a structured report:
      { query, person, summary, confidence, sources, matches, workers_used, latency_ms }

    This is the ONE tool the agent needs — it never has to know which workers exist. Adding a new source
    is a new worker file; this tool's signature never changes.
    """
    return await person_lookup(query)


if __name__ == "__main__":
    mcp.run()
