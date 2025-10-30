"""Simple in-memory cache utilities for the backend."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

_DEFAULT_TTL = 60  # seconds
_CACHE: dict[str, tuple[datetime, Any]] = {}

# Métriques de cache pour le monitoring
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "invalidations": 0,
}


def get(key: str) -> Any | None:
    """Get a value from cache, updating statistics."""
    entry = _CACHE.get(key)
    if not entry:
        _cache_stats["misses"] += 1
        return None
    expires_at, value = entry
    if datetime.utcnow() >= expires_at:
        _CACHE.pop(key, None)
        _cache_stats["misses"] += 1
        return None
    _cache_stats["hits"] += 1
    return value


def set(key: str, value: Any, *, ttl: int = _DEFAULT_TTL) -> None:
    """Set a value in cache, updating statistics."""
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    _CACHE[key] = (expires_at, value)
    _cache_stats["sets"] += 1


def invalidate(prefix: str | None = None) -> None:
    """Invalidate cache entries, updating statistics."""
    if prefix is None:
        count = len(_CACHE)
        _CACHE.clear()
        _cache_stats["invalidations"] += count
        return
    keys_to_delete = [key for key in _CACHE if key.startswith(prefix)]
    for key in keys_to_delete:
        _CACHE.pop(key, None)
    _cache_stats["invalidations"] += len(keys_to_delete)


def get_stats() -> dict[str, Any]:
    """Get cache statistics for monitoring."""
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (
        _cache_stats["hits"] / total_requests * 100
        if total_requests > 0
        else 0.0
    )
    
    return {
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "sets": _cache_stats["sets"],
        "invalidations": _cache_stats["invalidations"],
        "hit_rate": round(hit_rate, 2),
        "total_requests": total_requests,
        "current_size": len(_CACHE),
    }


def reset_stats() -> None:
    """Reset cache statistics (useful for testing)."""
    _cache_stats["hits"] = 0
    _cache_stats["misses"] = 0
    _cache_stats["sets"] = 0
    _cache_stats["invalidations"] = 0
