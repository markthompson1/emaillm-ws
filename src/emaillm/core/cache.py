import os, hashlib, json, time
import redis
import re

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

def get_or_set(prompt: str, compute_fn):
    digest = _digest(prompt)
    key = f"cache:{digest}"
    cached = _redis.get(key)
    import logging
    log = logging.getLogger("emaillm")
    if cached:
        log.debug("cache_hit key=%s", digest[:12])
        return json.loads(cached), True
    reply = compute_fn(prompt)
    _redis.setex(key, _ttl, json.dumps(reply))
    log.debug("cache_miss key=%s", digest[:12])
    return reply, False
