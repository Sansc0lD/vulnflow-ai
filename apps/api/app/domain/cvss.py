"""CVSSCalculator — parses a CVSS v3.1 vector string and computes the FIRST base score.

Formula reference: FIRST.org CVSS v3.1 Specification Document §7.4 (Base score).
"""

import math
from decimal import Decimal

_PREFIX = "CVSS:3.1"

# FIRST CVSS v3.1 §7.4 base metric weight tables.
_ATTACK_VECTOR = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_ATTACK_COMPLEXITY = {"L": 0.77, "H": 0.44}
_PRIVILEGES_REQUIRED_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PRIVILEGES_REQUIRED_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}
_USER_INTERACTION = {"N": 0.85, "R": 0.62}
_SCOPE = {"U", "C"}
_IMPACT = {"H": 0.56, "L": 0.22, "N": 0.0}

_REQUIRED_METRICS = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")
_METRIC_TABLES = {
    "AV": _ATTACK_VECTOR,
    "AC": _ATTACK_COMPLEXITY,
    "UI": _USER_INTERACTION,
    "C": _IMPACT,
    "I": _IMPACT,
    "A": _IMPACT,
}


def _parse_vector(vector: str) -> dict[str, str]:
    if not vector.startswith(_PREFIX + "/"):
        raise ValueError(f"CVSS vector must start with '{_PREFIX}/': {vector!r}")

    segments = vector[len(_PREFIX) + 1 :].split("/")
    metrics: dict[str, str] = {}
    for segment in segments:
        parts = segment.split(":")
        if len(parts) != 2:
            raise ValueError(f"Malformed CVSS vector segment: {segment!r}")
        key, value = parts
        if key in metrics:
            raise ValueError(f"Duplicate CVSS metric: {key!r}")
        metrics[key] = value

    missing = [m for m in _REQUIRED_METRICS if m not in metrics]
    if missing:
        raise ValueError(f"Missing required CVSS base metric(s): {', '.join(missing)}")
    extra = set(metrics) - set(_REQUIRED_METRICS)
    if extra:
        raise ValueError(f"Unsupported CVSS metric segment(s): {', '.join(sorted(extra))}")

    if metrics["S"] not in _SCOPE:
        raise ValueError(f"Invalid value for metric S: {metrics['S']!r}")
    for key, table in _METRIC_TABLES.items():
        if metrics[key] not in table:
            raise ValueError(f"Invalid value for metric {key}: {metrics[key]!r}")
    pr_table = (
        _PRIVILEGES_REQUIRED_CHANGED if metrics["S"] == "C" else _PRIVILEGES_REQUIRED_UNCHANGED
    )
    if metrics["PR"] not in pr_table:
        raise ValueError(f"Invalid value for metric PR: {metrics['PR']!r}")

    return metrics


def _roundup(value: float) -> Decimal:
    """FIRST CVSS v3.1 Appendix A "Roundup" function — rounds up to the nearest 0.1."""
    int_input = round(value * 100000)
    if int_input % 10000 == 0:
        return Decimal(int_input) / Decimal(100000)
    return Decimal(math.floor(int_input / 10000) + 1) / Decimal(10)


def calculate_base_score(vector: str) -> Decimal:
    metrics = _parse_vector(vector)
    scope_changed = metrics["S"] == "C"

    pr_table = _PRIVILEGES_REQUIRED_CHANGED if scope_changed else _PRIVILEGES_REQUIRED_UNCHANGED
    exploitability = (
        8.22
        * _ATTACK_VECTOR[metrics["AV"]]
        * _ATTACK_COMPLEXITY[metrics["AC"]]
        * pr_table[metrics["PR"]]
        * _USER_INTERACTION[metrics["UI"]]
    )

    impact_base = 1 - (
        (1 - _IMPACT[metrics["C"]]) * (1 - _IMPACT[metrics["I"]]) * (1 - _IMPACT[metrics["A"]])
    )
    if impact_base <= 0:
        return Decimal("0.0")

    if scope_changed:
        impact = 7.52 * (impact_base - 0.029) - 3.25 * (impact_base - 0.02) ** 15
        base_score = min(1.08 * (impact + exploitability), 10.0)
    else:
        impact = 6.42 * impact_base
        base_score = min(impact + exploitability, 10.0)

    return _roundup(base_score)
