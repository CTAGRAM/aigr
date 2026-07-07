def plan(query: str) -> list[str]:

    q = query.lower()

    workers = [
        "memory",
        "tavily",
    ]

    developer_words = [
        "github",
        "developer",
        "engineer",
        "software",
        "programmer",
        "next.js",
        "react",
        "typescript",
        "python",
    ]

    if any(w in q for w in developer_words):
        workers.append("github")

    return workers
