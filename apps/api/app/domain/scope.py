"""ScopeEnforcer — FQDN/CIDR scope matching, SDD §2.5 UC-07d. EC-04: nested subdomains."""

import ipaddress


def _normalize_fqdn(host: str) -> str:
    return host.strip().lower().rstrip(".")


def _matches_domain_pattern(target: str, pattern: str) -> bool:
    pattern = _normalize_fqdn(pattern)
    if pattern.startswith("*."):
        base_domain = pattern[2:]
        return target == base_domain or target.endswith("." + base_domain)
    return target == pattern


def _matches_cidr(target: str, cidr: str) -> bool:
    try:
        target_ip = ipaddress.ip_address(target)
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False
    return target_ip in network


def is_target_in_scope(target_host: str, scope_entries: list[str]) -> bool:
    target = _normalize_fqdn(target_host)
    for entry in scope_entries:
        if "/" in entry:
            if _matches_cidr(target, entry):
                return True
        elif _matches_domain_pattern(target, entry):
            return True
    return False
