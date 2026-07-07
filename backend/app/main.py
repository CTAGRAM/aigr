"""FastAPI surface for the glasses + companion app.

Endpoints
  GET  /health                 liveness
  WS   /ws/ingest              stream audio bytes, or JSON {"type":"frame|audio|text","data":...}
  WS   /ws/events              live event stream — every turn/observation/action, for the app & dashboards
  POST /ingest                 one-shot ingest of an audio/text chunk (handy for curl testing)
  POST /ingest_frame           one JPEG camera frame (raw body) -> caption + observation memory
  POST /turn                   record a Gemini Live conversation turn into shared history + broadcast
  GET  /memories?kind=         list memories (kind=observation for what the camera saw)
  GET  /memories/search?q=     keyword search
  GET  /transcripts            recent transcripts

Requires: pip install -r requirements.txt (fastapi, uvicorn). The pipeline it drives is stdlib-only.
Run: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import base64
import json

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .config import build_orchestrator, build_stt, build_vision, load_settings
from .events import EventHub
from .memory.store import MemoryStore
from .pipeline import Pipeline

settings = load_settings()
memory = MemoryStore(settings.db_path)
pipeline = Pipeline(build_stt(settings), memory, build_orchestrator(settings), vision=build_vision(settings))
hub = EventHub()  # real-time sync spine shared by Gemini (turns) and Hermes (results)

app = FastAPI(title="aiGlass backend", version="0.1.0")


class IngestText(BaseModel):
    text: str
    speaker: str | None = None


class Turn(BaseModel):
    role: str                 # "user" | "assistant"
    text: str
    source: str = "gemini"    # gemini | hermes | app


@app.get("/health")
def health() -> dict:
    return {"ok": True, "stt": settings.stt_provider, "orchestrator": settings.orch_provider}


@app.post("/ingest")
async def ingest(body: IngestText) -> dict:
    # Text path: the MockSTT convention treats UTF-8 bytes as the transcript.
    result = pipeline.process(body.text.encode("utf-8"), speaker=body.speaker)
    await hub.publish({"type": "transcript", **result})
    return result


@app.post("/ingest_frame")
async def ingest_frame(request: Request) -> dict:
    # Raw JPEG bytes in the request body (what the Ray-Ban DAT app POSTs per frame).
    image = await request.body()
    result = pipeline.process_frame(image)
    if result.get("caption"):
        await hub.publish({"type": "observation", **result})
    return result


@app.post("/turn")
async def record_turn(turn: Turn) -> dict:
    """Log a live conversation turn (spoken via Gemini) into the shared history so Hermes sees it too,
    and broadcast it so every connected client stays in sync in real time."""
    memory_id = memory.add_memory("turn", f"[{turn.role}] {turn.text}", source=turn.source)
    event = {"type": "turn", "role": turn.role, "text": turn.text, "source": turn.source, "memory_id": memory_id}
    await hub.publish(event)
    return event


@app.get("/memories")
def list_memories(kind: str | None = None, limit: int = 100) -> list[dict]:
    return [m.__dict__ for m in memory.memories(kind=kind, limit=limit)]


@app.get("/memories/search")
def search_memories(q: str, limit: int = 10) -> list[dict]:
    return [m.__dict__ for m in memory.search_memories(q, limit=limit)]


@app.get("/transcripts")
def transcripts(limit: int = 50) -> list[dict]:
    return [t.__dict__ for t in memory.recent_transcripts(limit=limit)]


@app.websocket("/ws/ingest")
async def ws_ingest(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            msg = await ws.receive()
            if (data := msg.get("bytes")) is not None:
                result = pipeline.process(data)                       # raw bytes = audio
            elif (text := msg.get("text")) is not None:
                result = _handle_text_message(text)
            else:
                continue
            await ws.send_json(result)
            await _broadcast(result)
    except WebSocketDisconnect:
        return


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket) -> None:
    """Subscribe to the live event stream: turns, observations, and action results as they happen.
    The glasses app listens here to speak Hermes results the moment a task finishes."""
    await ws.accept()
    q = hub.subscribe()
    try:
        while True:
            await ws.send_json(await q.get())
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(q)


async def _broadcast(result: dict) -> None:
    """Fan a pipeline result out to /ws/events subscribers as a typed event."""
    if result.get("caption"):
        await hub.publish({"type": "observation", **result})
    elif result.get("transcript"):
        await hub.publish({"type": "transcript", **result})


def _handle_text_message(text: str) -> dict:
    """Route a WS text frame. A JSON envelope {"type","data"} lets the Ray-Ban app multiplex audio +
    camera frames over one socket; plain text falls back to the audio/transcript path."""
    try:
        env = json.loads(text)
    except ValueError:
        env = None
    if isinstance(env, dict) and "type" in env:
        kind, payload = env.get("type"), env.get("data", "")
        if kind == "frame":
            return pipeline.process_frame(base64.b64decode(payload))
        if kind == "audio":
            return pipeline.process(base64.b64decode(payload))
        if kind == "text":
            return pipeline.process(str(payload).encode("utf-8"))
    return pipeline.process(text.encode("utf-8"))
