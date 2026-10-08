from __future__ import annotations

import pytest

from src.validation.deployment_policy import _gate_is_clean


def valid_gate() -> dict:
    return {
        "publishable": True,
        "automatic_checks_passed": True,
        "manual_approval_valid": True,
        "checks": [{"id": "quality_report", "blocking": True, "passed": True}],
    }


def test_accepts_valid_publication_gate() -> None:
    assert _gate_is_clean(valid_gate()) is True


@pytest.mark.parametrize("checks", [[], [None], ["invalid"], [42], [{"passed": True}, None]])
def test_rejects_empty_or_malformed_checks(checks: list) -> None:
    gate = valid_gate()
    gate["checks"] = checks
    assert _gate_is_clean(gate) is False


def test_rejects_failed_blocking_check() -> None:
    gate = valid_gate()
    gate["checks"][0]["passed"] = False
    assert _gate_is_clean(gate) is False


def test_allows_failed_nonblocking_check() -> None:
    gate = valid_gate()
    gate["checks"][0]["blocking"] = False
    gate["checks"][0]["passed"] = False
    assert _gate_is_clean(gate) is True
