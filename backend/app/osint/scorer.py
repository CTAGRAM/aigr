from typing import Any


def merge_results(query: str, workers: list[Any]) -> dict:

    final = {
        "query": query,
        "confidence": 0.0,
        "summary": "",
        "sources": [],
        "matches": [],
    }

    confidences = []

    for worker in workers:

        if isinstance(worker, Exception):
            continue

        final["sources"].append({
            "provider": worker.get("provider", "unknown"),
            "latency_ms": worker.get("latency_ms", 0),
        })

        if worker.get("provider") == "memory":
            if worker.get("data"):
                confidences.append(1.0)

        if worker.get("provider") == "tavily":

            if worker.get("answer"):
                final["summary"] = worker["answer"]

            for r in worker.get("results", []):
                final["matches"].append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "score": r.get("score"),
                })

            confidences.append(0.75)

    if confidences:
        final["confidence"] = round(sum(confidences)/len(confidences),2)

    return final
