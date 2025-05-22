import hashlib
import json
import logging
import os
import re
from typing import Any, Callable, Tuple, TypeVar

import redis
import structlog

from .metrics import CACHE_HITS, CACHE_MISSES

logger = structlog.get_logger()
T = TypeVar('T')  # Generic type for the cached value

_url   = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_ttl   = int(os.getenv("CACHE_TTL_SECONDS", 604800))  # 7 days
_redis = redis.Redis.from_url(_url, decode_responses=True)

_NORMALISE_RE = re.compile(r"\s+")

def _normalise(prompt: str) -> str:
    """
    Collapse whitespace and lowercase so that cosmetic differences
    (extra spaces, new-lines, casing) hash to the same digest.
    """
    return _NORMALISE_RE.sub(" ", prompt.strip()).lower()

def _digest(prompt: str) -> str:
    return hashlib.sha256(_normalise(prompt).encode("utf-8")).hexdigest()

def get_or_set(prompt: str, compute_fn: Callable[[str], T], cache_name: str = "default") -> Tuple[T, bool]:
    """
    Get a value from cache or compute and cache it if not found.
    
    Args:
        prompt: The input prompt to use as cache key
        compute_fn: Function to compute the value if not in cache
        cache_name: Name of the cache for metrics (e.g., 'llm_responses', 'embeddings')
        
    Returns:
        Tuple of (value, was_cached) where was_cached is True if the value came from cache
    """
    digest = _digest(prompt)
    key = f"cache:{cache_name}:{digest}"
    
    # Try to get from cache
    start_time = time.time()
    cached = _redis.get(key)
    
    if cached is not None:
        # Cache hit
        duration = time.time() - start_time
        CACHE_HITS.labels(cache_name=cache_name).inc()
        logger.debug(
            "Cache hit",
            cache_name=cache_name,
            key=digest[:12],
            duration_seconds=duration
        )
        return json.loads(cached), True
    
    # Cache miss - compute and store
    logger.debug("Cache miss", cache_name=cache_name, key=digest[:12])
    CACHE_MISSES.labels(cache_name=cache_name).inc()
    
    reply = compute_fn(prompt)
    
    # Store in cache
    try:
        _redis.setex(key, _ttl, json.dumps(reply))
    except Exception as e:
        logger.error(
            "Failed to store in cache",
            cache_name=cache_name,
            key=digest[:12],
            error=str(e)
        )
    
    return reply, False
def get_redis() -> "redis.Redis":
    from emaillm.core.cache import _redis
    return _redis
