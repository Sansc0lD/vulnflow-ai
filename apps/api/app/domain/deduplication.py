"""DeduplicationService — SDD §5.2: dedup_hash = SHA256(project_id:cwe:host:port:path). EC-08."""

import hashlib


def compute_dedup_hash(
    *, project_id: str, cwe_id: str, host: str, port: int | None, endpoint_path: str
) -> str:
    # F4-MED-18: Use colon delimiters to prevent boundary collisions
    # (e.g. port=80, path="0/x" vs port=800, path="/x")
    port_component = str(port) if port is not None else ""
    raw = f"{project_id}:{cwe_id}:{host}:{port_component}:{endpoint_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
