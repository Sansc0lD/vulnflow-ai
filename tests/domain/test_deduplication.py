"""PLAN.md FASE 3.1 — DeduplicationService (SDD §5.2, EC-08)."""

import hashlib

from app.domain.deduplication import compute_dedup_hash


def test_dedup_hash_is_sha256_hex_digest() -> None:
    result = compute_dedup_hash(
        project_id="prj-1", cwe_id="CWE-89", host="app.klien.com", port=443, endpoint_path="/login"
    )

    assert len(result) == 64
    int(result, 16)  # raises ValueError if not valid hex


def test_dedup_hash_is_deterministic() -> None:
    kwargs = {
        "project_id": "prj-1",
        "cwe_id": "CWE-89",
        "host": "app.klien.com",
        "port": 443,
        "endpoint_path": "/login",
    }

    assert compute_dedup_hash(**kwargs) == compute_dedup_hash(**kwargs)


def test_dedup_hash_matches_manual_sha256_concatenation() -> None:
    result = compute_dedup_hash(
        project_id="prj-1", cwe_id="CWE-89", host="app.klien.com", port=443, endpoint_path="/login"
    )

    expected = hashlib.sha256(b"prj-1:CWE-89:app.klien.com:443:/login").hexdigest()
    assert result == expected


def test_dedup_hash_prevents_boundary_collision() -> None:
    # F4-MED-18: port 80 with path "0/x" vs port 800 with path "/x" must not collide
    h1 = compute_dedup_hash(
        project_id="prj-1", cwe_id="CWE-89", host="app.klien.com", port=80, endpoint_path="0/x"
    )
    h2 = compute_dedup_hash(
        project_id="prj-1", cwe_id="CWE-89", host="app.klien.com", port=800, endpoint_path="/x"
    )
    assert h1 != h2


def test_different_endpoint_path_produces_different_hash() -> None:
    # EC-08: endpoint_path must be part of the hash, otherwise distinct
    # findings on different endpoints get wrongly merged into one.
    base = {"project_id": "prj-1", "cwe_id": "CWE-89", "host": "app.klien.com", "port": 443}

    assert compute_dedup_hash(**base, endpoint_path="/login") != compute_dedup_hash(
        **base, endpoint_path="/admin"
    )


def test_different_port_produces_different_hash() -> None:
    base = {
        "project_id": "prj-1",
        "cwe_id": "CWE-89",
        "host": "app.klien.com",
        "endpoint_path": "/login",
    }

    assert compute_dedup_hash(**base, port=443) != compute_dedup_hash(**base, port=8443)


def test_null_port_produces_stable_hash_for_non_network_findings() -> None:
    # EC-09: non-network findings (e.g. manual entries) have no port.
    kwargs = {
        "project_id": "prj-1",
        "cwe_id": "CWE-79",
        "host": "app.klien.com",
        "port": None,
        "endpoint_path": "/search",
    }

    assert compute_dedup_hash(**kwargs) == compute_dedup_hash(**kwargs)
