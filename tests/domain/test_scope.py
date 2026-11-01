"""PLAN.md FASE 3.3 — ScopeEnforcer (SDD §2.5 UC-07d, EC-04 nested subdomains)."""

from app.domain.scope import is_target_in_scope


def test_wildcard_scope_matches_direct_subdomain() -> None:
    assert is_target_in_scope("app.klien.com", ["*.klien.com"]) is True


def test_wildcard_scope_matches_nested_subdomain() -> None:
    # EC-04: nested subdomains were wrongly flagged out-of-scope before FQDN
    # normalization was fixed.
    assert is_target_in_scope("staging.app.klien.com", ["*.klien.com"]) is True


def test_wildcard_scope_matches_bare_domain_itself() -> None:
    assert is_target_in_scope("klien.com", ["*.klien.com"]) is True


def test_exact_domain_scope_rejects_sibling_subdomain() -> None:
    assert is_target_in_scope("other.klien.com", ["app.klien.com"]) is False


def test_exact_domain_scope_matches_itself() -> None:
    assert is_target_in_scope("app.klien.com", ["app.klien.com"]) is True


def test_fqdn_normalization_handles_case_and_trailing_dot() -> None:
    assert is_target_in_scope("App.Klien.com.", ["*.klien.com"]) is True


def test_cidr_scope_matches_ip_in_range() -> None:
    assert is_target_in_scope("10.20.0.5", ["10.20.0.0/24"]) is True


def test_cidr_scope_rejects_ip_outside_range() -> None:
    assert is_target_in_scope("10.20.1.5", ["10.20.0.0/24"]) is False


def test_target_outside_every_scope_entry_is_out_of_scope() -> None:
    assert is_target_in_scope("evil.other.com", ["*.klien.com", "10.20.0.0/24"]) is False


def test_empty_scope_list_means_nothing_is_in_scope() -> None:
    assert is_target_in_scope("app.klien.com", []) is False
