"""
ALOA Cache — TTL-based in-memory cache for shell output and LLM answers.
Shared across all 10 features and the FastAPI server.
"""
import time
import hashlib
from typing import Any

# ── TTL tiers (seconds) ──────────────────────────────────────────────────────
STATIC      = 3600   # CPU model, OS info — never changes mid-session
SEMI_STATIC =  300   # RAM totals, process list (5 min)
DYNAMIC     =   60   # System stats, radar brief (1 min)
REALTIME    =   10   # Live CPU %, active ports (10 sec)


class TTLCache:
    def __init__(self, name: str = "cache"):
        self.name = name
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def remaining_ttl(self, key: str) -> int | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        _, expires_at = entry
        remaining = expires_at - time.monotonic()
        return max(0, int(remaining)) if remaining > 0 else None

    def purge_expired(self) -> int:
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if exp <= now]
        for k in expired:
            del self._store[k]
        return len(expired)


def normalize_key(text: str) -> str:
    return text.strip().lower()

def content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ── Global singletons (import these everywhere) ──────────────────────────────
api_cache     = TTLCache("api")       # FastAPI response cache
llm_cache     = TTLCache("llm")       # LLM answer cache (keyed by prompt hash)
system_cache  = TTLCache("system")    # psutil / shell output cache
