"""OSINT engine tunables (timeouts, retries, cache TTLs) via env, plus a re-export of the app settings
(which holds the API keys: tavily_api_key, github_token, ...)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from ..config import load_settings  # noqa: F401  (re-exported: holds API keys)


@dataclass
class OsintSettings:
    worker_timeout: float = float(os.getenv("OSINT_WORKER_TIMEOUT", "8"))
    worker_retries: int = int(os.getenv("OSINT_WORKER_RETRIES", "2"))
    worker_backoff: float = float(os.getenv("OSINT_WORKER_BACKOFF", "0.4"))
    worker_cache_ttl: int = int(os.getenv("OSINT_WORKER_CACHE_TTL", "600"))
    entity_cache_ttl: int = int(os.getenv("OSINT_ENTITY_CACHE_TTL", "86400"))
    summary_cache_ttl: int = int(os.getenv("OSINT_SUMMARY_CACHE_TTL", "86400"))
    max_workers: int = int(os.getenv("OSINT_MAX_WORKERS", "8"))


def osint_settings() -> OsintSettings:
    return OsintSettings()
