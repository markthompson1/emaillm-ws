import os, hashlib, json, time
import redis

_url   = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_ttl   = int(os.getenv("CACHE_TTL_SECONDS", 604800))  # 7 days
_redis = redis.Redis.from_url(_url, decode_responses=True)

def _digest(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

def get_or_set(prompt: str, compute_fn):
    key = f"cache:{_digest(prompt)}"
    cached = _redis.get(key)
    if cached:
        return json.loads(cached), True
    reply = compute_fn(prompt)
    _redis.setex(key, _ttl, json.dumps(reply))
    return reply, False
