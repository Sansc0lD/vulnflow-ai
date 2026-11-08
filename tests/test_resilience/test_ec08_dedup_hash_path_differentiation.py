"""PLAN.md FASE 7.2 — EC-08: Deduplication Hash Path Differentiation.

EDGE_CASES_AND_RESILIENCE.md §5.2 & §6 item 8:
If two vulnerabilities share the exact same host, port, and CWE (e.g. SQL Injection
on both `/search` and `/checkout`), ignoring the endpoint path would falsely merge
them into a single finding. `compute_dedup_hash` must differentiate them cleanly.
"""

from app.domain.deduplication import compute_dedup_hash


def test_ec08_distinct_endpoint_paths_produce_distinct_dedup_hashes() -> None:
    """Findings with different endpoint paths have different deduplication hashes."""
    project_id = "proj-100"
    cwe_id = "CWE-89"
    host = "target.corp.com"
    port = 443

    hash_path_a = compute_dedup_hash(
        project_id=project_id,
        cwe_id=cwe_id,
        host=host,
        port=port,
        endpoint_path="/api/v1/search",
    )
    hash_path_b = compute_dedup_hash(
        project_id=project_id,
        cwe_id=cwe_id,
        host=host,
        port=port,
        endpoint_path="/api/v1/users/export",
    )

    assert hash_path_a != hash_path_b
    assert len(hash_path_a) == 64
    assert len(hash_path_b) == 64


def test_ec08_identical_findings_produce_deterministic_identical_hash() -> None:
    """Exact same finding parameters on the same endpoint path match hash."""
    h1 = compute_dedup_hash(
        project_id="proj-100",
        cwe_id="CWE-79",
        host="app.example.com",
        port=80,
        endpoint_path="/comments",
    )
    h2 = compute_dedup_hash(
        project_id="proj-100",
        cwe_id="CWE-79",
        host="app.example.com",
        port=80,
        endpoint_path="/comments",
    )
    assert h1 == h2


def test_ec08_boundary_collision_prevention() -> None:
    """Colon delimiters prevent boundary collisions between port and path."""
    # e.g. port 80 with path "0/x" vs port 800 with path "/x"
    h1 = compute_dedup_hash(
        project_id="proj-1", cwe_id="CWE-89", host="app.com", port=80, endpoint_path="0/x"
    )
    h2 = compute_dedup_hash(
        project_id="proj-1", cwe_id="CWE-89", host="app.com", port=800, endpoint_path="/x"
    )
    assert h1 != h2
