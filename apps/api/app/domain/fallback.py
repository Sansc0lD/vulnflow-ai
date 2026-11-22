"""DeterministicFallbackEngine — UC-11b / EC-14: LLM quota-exhaustion/timeout fallback.

Loads `app/data/cwe_catalog.json` into memory once, giving O(1) lookups with
no per-request disk I/O or network dependency. Supports optional allowlisted
`tech_stack` tags so remediations reflect the target architecture without
exposing PoC or source code.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import NotRequired, TypedDict, cast

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "cwe_catalog.json"
_DEFAULT_CWE_KEY = "UNKNOWN"


class CWEFallbackEntry(TypedDict):
    title: str
    business_impact: str
    remediation: str
    stack_patterns: NotRequired[dict[str, str]]


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, CWEFallbackEntry]:
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        return cast(dict[str, CWEFallbackEntry], json.load(f))


def get_fallback_narrative(
    cwe_id: str, tech_stack: dict[str, str] | None = None
) -> CWEFallbackEntry:
    catalog = load_catalog()
    entry = catalog.get(cwe_id, catalog[_DEFAULT_CWE_KEY])
    patterns = entry.get("stack_patterns")
    if not tech_stack or not isinstance(patterns, dict):
        return entry

    matched_note: str | None = None
    for stack_key in ("framework", "language", "database"):
        val = tech_stack.get(stack_key)
        if val and val in patterns:
            matched_note = patterns[val]
            break

    if not matched_note:
        return entry

    return CWEFallbackEntry(
        title=entry["title"],
        business_impact=entry["business_impact"],
        remediation=f"{entry['remediation']} Stack guidance: {matched_note}",
    )
