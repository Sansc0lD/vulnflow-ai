"""PLAN.md FASE 3.5 — DeterministicFallbackEngine (UC-11b, EC-14: LLM quota/timeout fallback)."""

from app.domain.fallback import get_fallback_narrative, load_catalog


def test_get_fallback_narrative_returns_known_cwe_entry() -> None:
    narrative = get_fallback_narrative("CWE-89")

    assert narrative["title"]
    assert narrative["business_impact"]
    assert narrative["remediation"]


def test_get_fallback_narrative_falls_back_to_unknown_entry_for_unmapped_cwe() -> None:
    narrative = get_fallback_narrative("CWE-99999-DOES-NOT-EXIST")

    assert narrative == load_catalog()["UNKNOWN"]


def test_catalog_contains_unknown_default_entry() -> None:
    catalog = load_catalog()

    assert "UNKNOWN" in catalog
    assert all(key in catalog["UNKNOWN"] for key in ("title", "business_impact", "remediation"))


def test_load_catalog_is_cached_after_first_call() -> None:
    first = load_catalog()
    second = load_catalog()

    assert first is second  # same dict object: loaded from disk only once
