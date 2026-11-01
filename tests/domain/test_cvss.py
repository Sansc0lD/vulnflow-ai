"""PLAN.md FASE 3.2 — CVSSCalculator (parses CVSS v3.1 vector, FIRST base score formula)."""

from decimal import Decimal

import pytest
from app.domain.cvss import calculate_base_score


def test_calculate_base_score_critical_unchanged_scope() -> None:
    # SDD §2.6.1 reference vector/score pair.
    score = calculate_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    assert score == Decimal("9.8")


def test_calculate_base_score_low_unchanged_scope() -> None:
    # SDD example "Git Config File Disclosure".
    score = calculate_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N")
    assert score == Decimal("5.3")


def test_calculate_base_score_scope_changed_caps_at_ten() -> None:
    score = calculate_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
    assert score == Decimal("10.0")


def test_calculate_base_score_all_none_is_zero() -> None:
    score = calculate_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
    assert score == Decimal("0.0")


def test_calculate_base_score_rejects_missing_prefix() -> None:
    with pytest.raises(ValueError, match="CVSS:3.1"):
        calculate_base_score("AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")


def test_calculate_base_score_rejects_missing_metric() -> None:
    with pytest.raises(ValueError, match="AC"):
        calculate_base_score("CVSS:3.1/AV:N/PR:N/UI:N/S:U/C:H/I:H/A:H")


def test_calculate_base_score_rejects_invalid_metric_value() -> None:
    with pytest.raises(ValueError, match="AV"):
        calculate_base_score("CVSS:3.1/AV:X/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")


def test_calculate_base_score_rejects_unparseable_segment() -> None:
    with pytest.raises(ValueError, match="segment"):
        calculate_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/GARBAGE")
