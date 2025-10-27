"""Simple in-memory cache utilities for the backend."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

_DEFAULT_TTL = 60  # seconds
_CACHE: dict[str, tuple[datetime, Any]] = {}


def get(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if datetime.utcnow() >= expires_at:
        _CACHE.pop(key, None)
        return None
    return value


def set(key: str, value: Any, *, ttl: int = _DEFAULT_TTL) -> None:
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    _CACHE[key] = (expires_at, value)


def invalidate(prefix: str | None = None) -> None:
    if prefix is None:
        _CACHE.clear()
        return
    keys_to_delete = [key for key in _CACHE if key.startswith(prefix)]
    for key in keys_to_delete:
        _CACHE.pop(key, None)
