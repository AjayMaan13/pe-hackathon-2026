import os

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            db=int(os.environ.get("REDIS_DB", 0)),
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
            decode_responses=True,
            # No retries: a Redis outage should fail this lookup in
            # milliseconds and fall through to Postgres, not add multi-second
            # latency to every redirect while redis-py retries.
            retry=Retry(NoBackoff(), 0),
            retry_on_error=[],
        )
    return _client


def _key(short_code: str) -> str:
    return f"url:{short_code}"


def get_cached_url(short_code: str) -> str | None:
    """Read-through cache lookup. Any Redis error (down, timeout, refused)
    is treated as a miss so the caller falls back to Postgres — the cache
    is an optimization, not a dependency the redirect path can't survive
    without."""
    try:
        return _get_client().get(_key(short_code))
    except redis.RedisError:
        return None


def set_cached_url(short_code: str, original_url: str) -> None:
    ttl = int(os.environ.get("REDIS_TTL_SECONDS", 3600))
    try:
        _get_client().set(_key(short_code), original_url, ex=ttl)
    except redis.RedisError:
        pass
