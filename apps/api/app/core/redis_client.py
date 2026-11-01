"""Redis client config & distributed lock — PLAN.md FASE 4.7 (EC-15)."""

import contextlib
import os
import threading
from typing import Protocol

import redis


class RedisLike(Protocol):
    """The minimal redis.Redis surface DistributedLock needs — lets tests
    inject an in-memory fake instead of requiring a live Redis server."""

    def set(
        self, key: str, value: str, *, nx: bool = False, ex: int | None = None
    ) -> bool | None: ...
    def get(self, key: str) -> str | None: ...
    def delete(self, key: str) -> None: ...


def get_redis_url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL environment variable is not set.")
    return url


_client: redis.Redis | None = None
_client_lock = threading.Lock()


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = redis.Redis.from_url(get_redis_url(), decode_responses=True)
    return _client


class DistributedLock:
    """EC-15 — prevents a double-clicked "Export PDF" from enqueueing two
    compile jobs; a second request while the lock is held gets back the
    SAME job_id via `current_holder()` instead of starting a new job."""

    def __init__(self, client: RedisLike, *, key: str, ttl_seconds: int) -> None:
        self._client = client
        self._key = key
        self._ttl_seconds = ttl_seconds

    def acquire(self, holder_value: str) -> bool:
        return bool(self._client.set(self._key, holder_value, nx=True, ex=self._ttl_seconds))

    def current_holder(self) -> str | None:
        return self._client.get(self._key)

    def release(self, holder_value: str | None = None) -> bool:
        """F4-MED-01: atomic compare-and-delete to ensure only the holder releases the lock."""
        if holder_value is None:
            self._client.delete(self._key)
            return True

        if hasattr(self._client, "eval"):
            lua = (
                "if redis.call('get', KEYS[1]) == ARGV[1] then "
                "return redis.call('del', KEYS[1]) "
                "else return 0 end"
            )
            with contextlib.suppress(Exception):
                res = self._client.eval(lua, 1, self._key, holder_value)
                return bool(res)

        if self._client.get(self._key) == holder_value:
            self._client.delete(self._key)
            return True
        return False
