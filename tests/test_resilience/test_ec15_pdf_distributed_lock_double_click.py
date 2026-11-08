"""PLAN.md FASE 7.2 — EC-15: PDF Export Distributed Lock Double-Click Prevention.

EDGE_CASES_AND_RESILIENCE.md §5.3 & §6 item 15:
When a user rapidly double-clicks the "Export PDF" button (especially when their
remaining monthly report quota is 1), the system must not launch duplicate Celery
tasks or double-decrement quota. A Redis distributed lock (`lock:report:{project_id}`,
TTL 10s) returns the existing in-flight `job_id` to the second request.
"""

from app.core.redis_client import DistributedLock


class _FakeRedisClient:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def delete(self, key: str) -> None:
        self.data.pop(key, None)

    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> int:
        key, expected = keys_and_args[0], keys_and_args[1]
        if self.data.get(key) == expected:
            del self.data[key]
            return 1
        return 0


def test_ec15_distributed_lock_prevents_duplicate_compilation_and_returns_same_holder() -> None:
    """Acquiring a held lock fails and surfaces the current job holder."""
    redis = _FakeRedisClient()
    lock_key = "lock:report:project-uuid-999"

    lock_first = DistributedLock(redis, key=lock_key, ttl_seconds=10)
    lock_second = DistributedLock(redis, key=lock_key, ttl_seconds=10)

    # Click 1: Lock is unheld -> acquire succeeds with temporary token
    assert lock_first.current_holder() is None
    acquired = lock_first.acquire("job-celery-101")
    assert acquired is True
    assert lock_first.current_holder() == "job-celery-101"

    # Click 2 (rapid double-click): Lock is already held by job-celery-101
    assert lock_second.current_holder() == "job-celery-101"
    acquired_second = lock_second.acquire("job-celery-102")
    assert acquired_second is False  # Rejected!

    # Second caller receives the existing active job_id
    replayed_job_id = lock_second.current_holder()
    assert replayed_job_id == "job-celery-101"


def test_ec15_release_distributed_lock_safe_compare_and_delete() -> None:
    """Releasing the lock only succeeds if the caller holds the token."""
    redis = _FakeRedisClient()
    lock = DistributedLock(redis, key="lock:report:p1", ttl_seconds=10)

    lock.acquire("worker-token-alpha")
    # Imposter tries to release -> fails
    released_imposter = lock.release("imposter-token")
    assert released_imposter is False
    assert lock.current_holder() == "worker-token-alpha"

    # Legitimate owner releases -> succeeds
    released_owner = lock.release("worker-token-alpha")
    assert released_owner is True
    assert lock.current_holder() is None
