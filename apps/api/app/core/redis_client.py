"""Redis client config & distributed lock — PLAN.md FASE 4.7 (EC-15)."""

import contextlib
import os
import threading
from collections.abc import Callable
from typing import Any, Protocol

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


def get_redis_client_factory() -> Callable[[], Any]:
    """Injects the *function*, not a connected client.

    For an endpoint where Redis is only needed conditionally (e.g. ingest's
    optional `Idempotency-Key` gate), a plain `Depends(get_redis_client)`
    would call `get_redis_client()` — and therefore require `REDIS_URL` to be
    configured — on every single request to that route, even ones that never
    touch Redis. Depending on this factory instead defers that call (and its
    potential `RuntimeError`) until the endpoint body actually needs it.

    Returns `Callable[[], Any]`, not `Callable[[], RedisLike]`, for the same
    reason `reports.py` types its own `Depends(get_redis_client)` as `Any`:
    the real `redis.Redis` isn't declared against the `RedisLike` Protocol,
    so mypy can't verify structural compatibility at this boundary — only
    `DistributedLock.__init__`'s `client: RedisLike` parameter actually
    enforces the shape once a caller passes a value in.
    """
    return get_redis_client


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
