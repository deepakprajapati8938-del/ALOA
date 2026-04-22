"""
ALOA Cache — Simple TTL-based in-memory cache.

Two global singletons are used across the app:
  - command_cache: caches raw shell command output
  - answer_cache:  caches final LLM-interpreted answers keyed by question
"""
import time
import hashlib
from typing import Any


# ── TTL constants ─────────────────────────────────────────────────────────────
STATIC     = 3600   # hostname, CPU model, OS version — rarely changes
SEMI_STATIC =  300  # RAM total, username, uptime (5 min)
DYNAMIC    =   30   # IP, battery, active adapters (30 sec)
REALTIME   =   10   # current time, processes, ports (10 sec)


class TTLCache:
    """Thread-safe-enough in-process TTL cache."""

    def __init__(self, name: str = "cache"):
        self.name = name
        self._store: dict[str, tuple[Any, float]] = {}

    # ── core ops ──────────────────────────────────────────────────────────────

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

    def purge_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if exp <= now]
        for k in expired:
            del self._store[k]
        return len(expired)

    # ── helpers ───────────────────────────────────────────────────────────────

    def remaining_ttl(self, key: str) -> int | None:
        """Return seconds until expiry, or None if not cached."""
        entry = self._store.get(key)
        if entry is None:
            return None
        _, expires_at = entry
        remaining = expires_at - time.monotonic()
        return max(0, int(remaining)) if remaining > 0 else None

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"TTLCache(name={self.name!r}, entries={len(self)})"


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_key(text: str) -> str:
    """Normalise a question/command string into a stable cache key."""
    return text.strip().lower()


def content_hash(text: str) -> str:
    """Short hash of text content — used to key answer cache on output."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


# ── Global singletons ─────────────────────────────────────────────────────────

command_cache = TTLCache("command")   # raw shell output, keyed by command string
answer_cache  = TTLCache("answer")    # LLM answers, keyed by normalised question
