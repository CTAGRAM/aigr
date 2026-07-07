from cachetools import TTLCache

person_cache = TTLCache(
    maxsize=500,
    ttl=86400,
)
