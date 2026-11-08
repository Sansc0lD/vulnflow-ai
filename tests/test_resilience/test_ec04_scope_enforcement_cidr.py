"""PLAN.md FASE 7.2 — EC-04: Scope Enforcement & CIDR Normalization.

SRS UC-07d & EDGE_CASES_AND_RESILIENCE.md §6 item 4:
Nested subdomains (e.g. `api.v2.internal.target.com`) and IPv4/IPv6 CIDR ranges
must be accurately evaluated by `ScopeEnforcer` so that legitimate target assets
are not wrongly quarantined while unauthorized targets are quarantined.
"""

import pytest
from app.domain.scope import is_target_in_scope


@pytest.mark.parametrize(
    ("target", "scope_rules", "expected"),
    [
        # Deeply nested subdomains matching wildcard
        ("deeply.nested.sub.domain.corp.com", ["*.corp.com"], True),
        ("v1.api.staging.auth.corp.com", ["*.auth.corp.com"], True),
        ("v1.api.staging.auth.corp.com", ["*.corp.com"], True),
        # Base domain itself matches wildcard
        ("corp.com", ["*.corp.com"], True),
        # Case insensitivity and trailing root dots
        ("API.CORP.COM.", ["*.corp.com"], True),
        ("auth.corp.com", ["AUTH.CORP.COM."], True),
        # Sibling or prefix-alike domain injection prevention
        ("notcorp.com", ["*.corp.com"], False),
        ("evil-corp.com", ["*.corp.com"], False),
        ("attacker.com", ["*.corp.com"], False),
        # IPv4 CIDR matching
        ("192.168.1.45", ["192.168.1.0/24"], True),
        ("192.168.2.1", ["192.168.1.0/24"], False),
        ("10.0.0.1", ["10.0.0.0/8"], True),
        ("11.0.0.1", ["10.0.0.0/8"], False),
        # Single IP entry
        ("192.168.1.100", ["192.168.1.100/32"], True),
        ("192.168.1.101", ["192.168.1.100/32"], False),
    ],
)
def test_ec04_scope_enforcement_nested_subdomains_and_cidr(
    target: str, scope_rules: list[str], expected: bool
) -> None:
    assert is_target_in_scope(target, scope_rules) is expected
