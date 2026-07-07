import asyncio

from .cache import person_cache
from .planner import plan
from .scorer import merge_results
from .workers import WORKERS


async def lookup_person(query: str):

    if query in person_cache:
        return person_cache[query]

    worker_names = plan(query)

    tasks = [
        WORKERS[name](query)
        for name in worker_names
        if name in WORKERS
    ]

    results = await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )

    merged = merge_results(
        query=query,
        workers=results,
    )

    person_cache[query] = merged

    return merged
