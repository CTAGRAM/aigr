# OSINT Intelligence Engine (`app/osint/`)

Turns a natural-language lookup ("who is Guillermo Rauch") into a scored, entity-resolved intelligence
report by fanning out to parallel workers, resolving them into one canonical entity, building a knowledge
graph, scoring the evidence, and summarizing.

Exposed to the agent as **one** MCP tool: `aiglass_person_lookup(query)` — Claude never needs to know
which workers exist. Also available over HTTP: `POST /osint/lookup` and streaming `WS /ws/osint`.

## Pipeline

```
plan → execute → resolve → graph → merge → score → summarize
```

The **engine knows nothing about worker internals**. It only calls: planner (which workers), registry
(run them), resolver (canonical entity), knowledge graph (store), merger (assemble evidence), scorer
(confidence), summarizer (spoken text).

## Module map

| File | Role |
|---|---|
| `result.py` | `WorkerResult` — the contract every worker returns (never a raw dict) |
| `entity.py` | `Person`, `EntityType`, `Relationship` |
| `workers/base.py` | `@worker(...)` — timeout + retry(exp backoff) + cache + logging; guarantees a `WorkerResult` |
| `workers/*.py` | data sources: memory, tavily, github, company (Wikipedia), conference, … |
| `registry.py` | **dynamic** discovery + parallel isolated execution (add a worker = zero engine edits) |
| `planner.py` | heuristic worker selection · `llm/planner.py` = optional LLM planning |
| `resolver.py` | merge many `WorkerResult`s → one `Person` |
| `merger.py` / `scorer.py` | assemble evidence · score confidence (source quality × self-confidence × corroboration) |
| `graph/` | `KnowledgeGraph` over `GraphStore` (SQLite now; Neo4j/Qdrant/LanceDB later) + embeddings/semantic search |
| `engine.py` | orchestrates the pipeline; `run()` (alias `lookup_person`) |
| `streaming.py` | `run_streaming()` — per-worker progress events for the WebSocket |
| `llm/` | summarizer / planner / verifier — all with deterministic fallbacks (no hard LLM dep) |
| `cache.py` | multi-level TTL (worker/entity/summary); cachetools or stdlib fallback |
| `settings.py` / `logging.py` | tunables (timeouts/retries/TTLs) · structured logging |

## Adding a worker (the whole point of the design)

Create `workers/reddit.py`:

```python
import httpx
from ..result import WorkerResult
from .base import worker

@worker("reddit", timeout=10)          # timeout + retry + cache + logging come free
async def reddit_worker(query: str) -> WorkerResult:
    async with httpx.AsyncClient(timeout=8) as c:
        r = await c.get("https://www.reddit.com/search.json", params={"q": query})
        r.raise_for_status()
        return WorkerResult(provider="reddit", success=True, confidence=0.5, data=r.json())
```

Then add `"reddit"` to `planner.plan()` when relevant. **No engine/registry edits.** The registry
auto-discovers it; a missing optional dependency just skips the worker (never fatal).

> Implemented workers: `memory`, `tavily`, `github`, `company`, `conference`.
> The same 6-line pattern adds `reddit`, `hackernews`, `youtube`, `website`, `docs`, `podcast`,
> `email`, `calendar`, `local` — add them incrementally as their sources/keys become available.

## Guarantees (spec compliance)

- Every worker returns `WorkerResult` — enforced by `@worker`.
- Async throughout; type hints; structured logging (start/finish/latency/error/cache-hit).
- Timeout (`asyncio.wait_for`) + retries (exp backoff on timeout/network/429/5xx) per worker.
- **One worker's failure never fails the lookup** (registry isolation + graceful `WorkerResult.failed`).
- Storage behind interfaces: swap SQLite→Neo4j/Qdrant (graph) or the TTL cache→Redis with no engine change.

## Performance targets (& where they're met)

| Target | Status |
|---|---|
| Memory lookup < 30ms | ✅ ~13ms measured |
| Planner < 10ms | ✅ pure heuristic |
| Cached lookup < 250ms | ✅ entity cache short-circuits |
| Parallel workers 3–6s | ✅ bounded by per-worker timeouts, run concurrently |

## Tests

```bash
cd backend
python3 app/osint/tests/test_osint.py          # spine: base/registry/planner/resolver/merger/scorer/engine
python3 app/osint/tests/test_graph.py          # knowledge graph + semantic rerank
python3 app/osint/tests/test_llm_streaming.py  # llm fallbacks + streaming + worker registration
```
All run with zero third-party deps (cache + LLM fall back; network workers skip gracefully). 18/18 green.

## Deploy (AWS)

- **Docker:** `backend/Dockerfile` → `docker build -t aiglass-backend backend && docker run -p 8000:8000 aiglass-backend`.
- **EC2 / Lightsail + systemd:** already used for the core backend (`deploy/aws/`). The OSINT routes ride
  along in the same `aiglass-backend` service; the MCP tool rides in `aiglass-mcp`.
- **Redis (scale-out cache):** replace the `_TTLCache` instances in `cache.py` with a Redis client — the
  `__contains__/__getitem__/__setitem__/get` interface is all the code uses.
- **Postgres / Qdrant (graph at scale):** implement `graph.GraphStore` against Postgres (pgvector) or
  Qdrant and pass it to `KnowledgeGraph(store=...)`; nothing else changes.

## Backward compatibility

Nothing was removed. `public_search` / `aiglass_public_search`, `lookup_person`, `merge_results`, and the
original `WorkerResult` fields all still work; the OSINT routes are additive and fail-safe (wrapped so an
import error can never stop the core backend booting).
