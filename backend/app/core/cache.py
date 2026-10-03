"""A small in-process TTL cache.

Phase 7 needs to keep the hot read paths (the application metadata the builder
loads on every navigation) off the database without introducing a new
dependency such as Redis. That is all this does: a dict, a deadline per entry and
a lock, so it stays correct when the ASGI server handles requests on several
threads.

Two rules keep it safe to use here:

* entries expire on their own, so a forgotten invalidation cannot serve stale
  data forever;
* nothing but plain, already-serialised data goes in. Cached ORM objects would
  outlive the session they were loaded in.
"""

import os
import threading
import time
from typing import Any, Callable, Dict, Optional


class TTLCache:
    """Key/value store whose entries expire after ``ttl_seconds``."""

    def __init__(self, ttl_seconds: float = 5.0, max_entries: int = 128):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: Dict[Any, tuple] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Optional[Any]:
        """Return the cached value, or ``None`` when absent or expired."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if expires_at <= time.monotonic():
                del self._entries[key]
                self.misses += 1
                return None
            self.hits += 1
            return value

    def set(self, key: Any, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Store ``value`` under ``key``, evicting the oldest entry when full."""
        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
        with self._lock:
            if key not in self._entries and len(self._entries) >= self.max_entries:
                oldest = min(self._entries, key=lambda k: self._entries[k][0])
                del self._entries[oldest]
            self._entries[key] = (time.monotonic() + ttl, value)

    def get_or_set(self, key: Any, factory: Callable[[], Any], ttl_seconds: Optional[float] = None) -> Any:
        """Return the cached value, computing and storing it on a miss.

        The factory runs while holding the lock on purpose: these caches back
        expensive metadata assemblies, and letting a thundering herd of requests
        all run the same query is worse than the brief serialisation.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and entry[0] > time.monotonic():
                self.hits += 1
                return entry[1]
            if entry is not None:
                del self._entries[key]
            self.misses += 1
            value = factory()
            ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
            if len(self._entries) >= self.max_entries:
                oldest = min(self._entries, key=lambda k: self._entries[k][0])
                del self._entries[oldest]
            self._entries[key] = (time.monotonic() + ttl, value)
            return value

    def invalidate(self, key: Any) -> None:
        """Drop one entry."""
        with self._lock:
            self._entries.pop(key, None)

    def invalidate_prefix(self, prefix: Any) -> int:
        """Drop every entry whose key starts with ``prefix``; returns the count."""
        with self._lock:
            doomed = [key for key in self._entries if key == prefix or str(key).startswith(str(prefix))]
            for key in doomed:
                del self._entries[key]
            return len(doomed)

    def clear(self) -> None:
        """Drop every entry and reset the counters."""
        with self._lock:
            self._entries.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Hit/miss counters plus the live entry count, for tests and /health."""
        with self._lock:
            return {
                "entries": len(self._entries),
                "hits": self.hits,
                "misses": self.misses,
                "ttl_seconds": self.ttl_seconds,
                "max_entries": self.max_entries,
            }


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# Application metadata assembled by the builder: read on every navigation,
# rewritten only when someone edits the application.
application_metadata_cache = TTLCache(
    ttl_seconds=_float_env("METADATA_CACHE_TTL", 5.0),
    max_entries=_int_env("METADATA_CACHE_MAX_ENTRIES", 64),
)