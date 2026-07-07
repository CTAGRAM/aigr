"""Heuristic planner — decides which workers to run for a query. (LLM planning is the optional upgrade in
llm/planner.py.) The engine never hardcodes workers; it asks the planner.
"""
from __future__ import annotations

_DEVELOPER_WORDS = (
    "github", "developer", "engineer", "software", "programmer",
    "next.js", "react", "typescript", "python", "rust", "golang", "open source",
)
_CONFERENCE_WORDS = ("conference", "summit", "keynote", "speaker", "talk", "meetup")


def plan(query: str) -> list[str]:
    q = query.lower()
    workers = ["memory", "tavily", "company"]   # memory + web + wikipedia enrichment: broadly useful
    if any(w in q for w in _DEVELOPER_WORDS):
        workers.append("github")
    if any(w in q for w in _CONFERENCE_WORDS):
        workers.append("conference")
    return workers
