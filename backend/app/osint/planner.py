"""Heuristic planner — decides which workers to run for a query. (LLM planning is the optional upgrade in
llm/planner.py, enabled via OSINT_LLM_PLANNER=1.) The engine never hardcodes workers; it asks the planner.
"""
from __future__ import annotations

import re

_DEVELOPER_WORDS = (
    "github", "developer", "engineer", "software", "programmer",
    "next.js", "react", "typescript", "python", "rust", "golang", "open source",
)
_CONFERENCE_WORDS = ("conference", "summit", "keynote", "speaker", "talk", "meetup")
_VIDEO_WORDS = ("video", "youtube", "tutorial", "interview")
_PODCAST_WORDS = ("podcast", "episode", "show host")
_REDDIT_WORDS = ("reddit", "opinion", "review", "discussion", "community", "thread")
_EMAIL_WORDS = ("email", "inbox", "mailbox")
_CALENDAR_WORDS = ("calendar", "schedule", "meeting", "appointment", "agenda")
_DOCS_WORDS = ("documentation", "api reference", "docs for")
_LOCAL_WORDS = ("nearby", "on device", "my files", "local file")
_DOMAIN = re.compile(r"\b[a-z0-9-]+\.(com|io|org|net|dev|ai|co|xyz|app|me|so|gg|tv)\b", re.I)


def plan(query: str) -> list[str]:
    q = query.lower()
    workers = ["memory", "tavily", "company"]   # memory + web + wikipedia: broadly useful

    if any(w in q for w in _DEVELOPER_WORDS):
        workers += ["github", "hackernews"]
    if any(w in q for w in _CONFERENCE_WORDS):
        workers.append("conference")
    if any(w in q for w in _VIDEO_WORDS):
        workers.append("youtube")
    if any(w in q for w in _PODCAST_WORDS):
        workers.append("podcast")
    if any(w in q for w in _REDDIT_WORDS):
        workers.append("reddit")
    if _DOMAIN.search(q) or "http" in q:
        workers.append("website")
    if any(w in q for w in _EMAIL_WORDS):
        workers.append("email")
    if any(w in q for w in _CALENDAR_WORDS):
        workers.append("calendar")
    if any(w in q for w in _DOCS_WORDS):
        workers.append("docs")
    if any(w in q for w in _LOCAL_WORDS):
        workers.append("local")

    seen: set[str] = set()
    ordered: list[str] = []
    for w in workers:
        if w not in seen:
            seen.add(w)
            ordered.append(w)
    return ordered
