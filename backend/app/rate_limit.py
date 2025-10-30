"""Simple rate limiting implementation without external dependencies."""

import time
from collections import defaultdict
from typing import Dict, Tuple

# Store: {endpoint_ip: [(timestamp, count), ...]}
_rate_limit_store: Dict[str, list[Tuple[float, int]]] = defaultdict(list)


def check_rate_limit(endpoint: str, client_ip: str | None, requests_per_minute: int) -> bool:
    """
    Check if a request exceeds the rate limit.
    
    Returns True if allowed, False if rate limited.
    """
    if not client_ip:
        # If we can't identify the client, allow the request
        return True
    
    key = f"{endpoint}:{client_ip}"
    current_time = time.time()
    one_minute_ago = current_time - 60
    
    # Clean old entries
    if key in _rate_limit_store:
        _rate_limit_store[key] = [
            (ts, count) for ts, count in _rate_limit_store[key]
            if ts > one_minute_ago
        ]
    
    # Count requests in the last minute
    request_count = sum(count for _, count in _rate_limit_store[key])
    
    if request_count >= requests_per_minute:
        return False
    
    # Add this request
    if key in _rate_limit_store and _rate_limit_store[key]:
        # Update the latest entry
        _rate_limit_store[key][-1] = (current_time, request_count + 1)
    else:
        _rate_limit_store[key] = [(current_time, 1)]
    
    return True


def get_rate_limit_key(endpoint: str, client_ip: str | None, requests_per_minute: int) -> str:
    """Get the key for storing rate limit data."""
    if not client_ip:
        return f"{endpoint}:unknown"
    return f"{endpoint}:{client_ip}:{requests_per_minute}"


def reset_rate_limit_store() -> None:
    """Clear the in-memory rate limit store (useful for tests)."""
    _rate_limit_store.clear()
