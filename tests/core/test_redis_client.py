"""PLAN.md FASE 4.7 — Redis client config + distributed lock (EC-15)."""

import pytest
from app.core.redis_client import (
    DistributedLock,
    get_redis_client,
    get_redis_client_factory,
    get_redis_url,
)


class _FakeRedis:
    """Minimal in-memory double for the subset of redis.Redis used here."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def set(self, key: str, value: str, *, nx: bool = False, ex: int | None = None) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


def test_get_redis_url_reads_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    assert get_redis_url() == "redis://localhost:6379/0"


def test_get_redis_url_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        get_redis_url()


def test_get_redis_client_factory_defers_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Must not require REDIS_URL just to obtain the factory — only calling
    # the returned function should (ingest.py's optional Idempotency-Key gate
    # relies on exactly this to stay usable without Redis configured).
    monkeypatch.delenv("REDIS_URL", raising=False)

    factory = get_redis_client_factory()

    assert factory is get_redis_client
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        factory()


def test_distributed_lock_acquire_succeeds_when_free() -> None:
    lock = DistributedLock(_FakeRedis(), key="lock:report:prj-1", ttl_seconds=10)
    assert lock.acquire("job-1") is True


def test_distributed_lock_acquire_fails_when_held() -> None:
    redis = _FakeRedis()
    lock = DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10)
    lock.acquire("job-1")

    second_lock = DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10)
    assert second_lock.acquire("job-2") is False


def test_distributed_lock_holder_returns_existing_job_id_on_double_click() -> None:
    # EC-15: a second "Export PDF" click while the lock is held must surface
    # the SAME job_id, not create a new compile job.
    redis = _FakeRedis()
    DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10).acquire("job-1")

    held_value = DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10).current_holder()
    assert held_value == "job-1"


def test_distributed_lock_release_frees_the_lock() -> None:
    redis = _FakeRedis()
    lock = DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10)
    lock.acquire("job-1")
    lock.release("job-1")

    assert DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10).acquire("job-2") is True


def test_distributed_lock_release_rejects_wrong_holder() -> None:
    # F4-MED-01: non-holder cannot release the lock
    redis = _FakeRedis()
    lock = DistributedLock(redis, key="lock:report:prj-1", ttl_seconds=10)
    lock.acquire("job-1")
    assert lock.release("job-wrong") is False
    assert lock.current_holder() == "job-1"
