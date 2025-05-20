"""
Very-first cut: rolling token bucket stored in Redis ZSETs.
All numbers are *questions* (1 Q = 1 inbound email), not tokens.
"""

import os, time, uuid, redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL)

PLANS = {
    # plan : (max_questions, window_seconds)
    "free":  (30,  7 * 24 * 3600),     # 30 Q / 7-day rolling
    "pro":   (300, 30 * 24 * 3600),
    "team":  (10_000, 30 * 24 * 3600), # pooled, soft cap
}

def _key(plan: str, user_or_team: str) -> str:
    return f"quota:{plan}:{user_or_team.lower()}"

def check_and_consume(user_email: str, plan: str = "free") -> bool:
    """Return True iff the caller is **allowed** to proceed."""
    limit, window = PLANS[plan]
    now  = int(time.time())
    key  = _key(plan, user_email)
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)   # drop expired
    pipe.zcard(key)                               # current usage
    pipe.execute()
    usage = r.zcard(key)
    if usage >= limit:
        print(f"quota_block {key}")
        return False
    r.zadd(key, {uuid.uuid4().hex: now})
    print(f"quota_hit {key}")
    return True
