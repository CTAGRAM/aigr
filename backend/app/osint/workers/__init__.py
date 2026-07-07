from .memory import memory_worker
from .tavily import tavily_worker

WORKERS = {
    "memory": memory_worker,
    "tavily": tavily_worker,
}
