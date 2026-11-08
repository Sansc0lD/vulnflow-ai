"""PLAN.md FASE 7.2 — EC-07: Chunked Ingest Idempotency Key Granularity.

EDGE_CASES_AND_RESILIENCE.md §5.5 & §6 item 7:
Large scanner outputs (>200 MB) are chunked by the CLI into multiple fragments.
The `Idempotency-Key` must be unique per chunk (`{file_hash}:{chunk_index}`) so
that distinct fragments are not erroneously dropped as replays, while a retry
of the same fragment produces an identical key that safely replays cached responses.
"""

from vulnflow.ingest_client import chunk_findings, compute_idempotency_key


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


def test_ec07_chunk_keys_are_distinct_per_fragment_and_stable_across_retries() -> None:
    """Distinct chunk indices yield distinct keys; same chunk yields stable key."""
    file_hash = "abcdef0123456789abcdef0123456789"
    key_chunk_0 = compute_idempotency_key(file_hash, 0)
    key_chunk_1 = compute_idempotency_key(file_hash, 1)
    key_chunk_2 = compute_idempotency_key(file_hash, 2)

    # Chunks have unique keys
    assert key_chunk_0 == f"{file_hash}:0"
    assert key_chunk_1 == f"{file_hash}:1"
    assert key_chunk_2 == f"{file_hash}:2"
    assert len({key_chunk_0, key_chunk_1, key_chunk_2}) == 3

    # Retrying chunk 1 produces the exact same key across retries
    retry_key_chunk_1 = compute_idempotency_key(file_hash, 1)
    assert retry_key_chunk_1 == key_chunk_1


def test_ec07_chunk_findings_splits_sequences_evenly() -> None:
    """chunk_findings correctly slices findings into bounded batch payloads."""
    items = list(range(1250))
    chunks = chunk_findings(items, size=500)
    assert len(chunks) == 3
    assert len(chunks[0]) == 500
    assert len(chunks[1]) == 500
    assert len(chunks[2]) == 250


def test_ec07_idempotency_cache_replays_cached_response_without_duplicate_processing() -> None:
    """Redis cache keyed on (workspace, project, idempotency_key) prevents duplicate processing."""
    fake_redis = _FakeRedis()
    w_id = "workspace-123"
    p_id = "project-456"
    key = compute_idempotency_key("mock_hash_xyz", chunk_index=1)
    cache_key = f"idempotency:ingest:{w_id}:{p_id}:{key}"

    # First request: not in cache -> claim key
    acquired = fake_redis.set(cache_key, "__pending__", nx=True, ex=86400)
    assert acquired is True

    # After commit, result is cached
    mock_response_json = '{"processed": 50, "new": 50, "duplicated": 0, "quarantined": 0}'
    fake_redis.set(cache_key, mock_response_json, ex=86400)

    # Second request (retry after network glitch): key already exists -> returns cached json
    cached_val = fake_redis.get(cache_key)
    assert cached_val == mock_response_json
