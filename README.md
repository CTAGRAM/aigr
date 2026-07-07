# aiGlass

Discreet, self-hosted AI glasses — an open build inspired by [Omi](https://github.com/BasedHardware/omi),
made *a little different*: audio **and** camera capture in an opaque purpose-built frame, a lean
self-hosted backend (no Firebase/Deepgram/Pusher), and an **agentic orchestrator brain**
([Hermes Agent](https://github.com/nousresearch/hermes-agent), OpenClaw pluggable) that doesn't just
*notice* action items — it *executes* them in a sandbox on your VPS.

> **Scope (locked):** Tier 1 "Discreet AI glasses" — camera + mic + open-ear speaker, **no display**.
> See [docs/ROADMAP.md](docs/ROADMAP.md) for why an invisible in-lens display in clear rimless frames
> is not physically DIY-buildable, and what we build instead.

## The loop that makes it useful

```
glasses (mic+cam) ──BLE──▶ phone app ──WS──▶ your VPS backend ──MCP──▶ Hermes (sandbox)
      ▲                                    (STT → memory → action items)        │
      └────────────── speaker / app notification ◀───── results ◀───────────────┘
```

Conversation is transcribed, distilled to memories + action items, and the action items are handed to
Hermes, which actually *does* them (send the email, run the code, book the thing) inside a sandbox and
reports back.

## Repo layout

| Path | What |
|---|---|
| `backend/` | Self-hostable FastAPI backend: capture → STT → memory → action items → orchestrator. **Built first** (see below). |
| `firmware/` | XIAO ESP32-S3 Sense firmware (camera + PDM mic + BLE). *Needs the physical board to flash.* |
| `app/` | Rebranded companion app (BLE pairing, streaming, transcript/memory/chat UI). |
| `docs/` | [Architecture](docs/ARCHITECTURE.md) · [Bill of materials](docs/BOM.md) · [Roadmap](docs/ROADMAP.md) |

## Status

- ✅ **Phase 1 — backend core** (this commit): pipeline runs end-to-end with mock providers, no cloud deps.
- ⬜ Phase 2 — Hermes on VPS via MCP
- ⬜ Phase 3 — ESP32-S3 firmware
- ⬜ Phase 4 — companion app

## Quickstart (backend core)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # server deps; core logic needs none of them
python -m pytest tests/ -q               # verify the pipeline with mock STT + mock orchestrator
uvicorn app.main:app --reload            # run the API (optional)
```

The core pipeline (`app/pipeline.py`) depends only on the Python standard library, so it runs and is
testable even where heavy ML wheels (torch/faster-whisper) aren't available yet — providers are pluggable.
