import time

from ...memory.store import MemoryStore
from ...config import load_settings


async def memory_worker(query: str):

    settings = load_settings()

    store = MemoryStore(settings.db_path)

    start = time.perf_counter()

    memories = store.search_memories(
        query,
        limit=10,
    )

    latency = int((time.perf_counter()-start)*1000)

    return {
        "provider":"memory",
        "success":True,
        "confidence":1.0 if memories else 0.0,
        "latency_ms":latency,
        "data":[m.__dict__ for m in memories]
    }
