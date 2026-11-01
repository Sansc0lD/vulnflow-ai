"""DeterministicFallbackEngine — UC-11b / EC-14: LLM quota-exhaustion/timeout fallback.

Loads `app/data/cwe_catalog.json` into memory once, giving O(1) lookups with
no per-request disk I/O or network dependency.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict, cast

_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "cwe_catalog.json"
_DEFAULT_CWE_KEY = "UNKNOWN"


class CWEFallbackEntry(TypedDict):
    title: str
    business_impact: str
    remediation: str


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, CWEFallbackEntry]:
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        return cast(dict[str, CWEFallbackEntry], json.load(f))


def get_fallback_narrative(cwe_id: str) -> CWEFallbackEntry:
    catalog = load_catalog()
    return catalog.get(cwe_id, catalog[_DEFAULT_CWE_KEY])
