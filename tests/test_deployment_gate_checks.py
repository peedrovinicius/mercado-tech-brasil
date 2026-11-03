from __future__ import annotations

import json
from pathlib import Path

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


@pytest.mark.parametrize(
    "checks",
    [
        [], [None], ["invalid"], [42], [{"passed": True}, None],
        [{}], [{"blocking": False}],
        [{"id": "optional", "blocking": False}],
        [{"id": "", "passed": True, "blocking": False}],
        [{"id": "  ", "passed": True, "blocking": True}],
        [{"id": 3, "passed": True, "blocking": True}],
        [{"id": "quality_report", "passed": "true", "blocking": True}],
        [{"id": "quality_report", "passed": True, "blocking": "false"}],
        [{"id": "quality_report", "passed": True, "blocking": 0}],
        [
            {"id": "same", "passed": True, "blocking": True},
            {"id": "same", "passed": True, "blocking": False},
        ],
    ],
)
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

def test_rejects_missing_or_invalid_summary_approvals() -> None:
    for field in ("publishable", "automatic_checks_passed", "manual_approval_valid"):
        for invalid in (False, None, 1, "true"):
            gate = valid_gate()
            gate[field] = invalid
            assert _gate_is_clean(gate) is False


def test_accepts_real_published_monthly_and_rais_gate_shapes() -> None:
    gold = Path(__file__).resolve().parents[1] / "data" / "gold"
    for path in [
        *sorted(gold.glob("publication-gate-*.json")),
        *sorted(gold.glob("rais-publication-gate-*.json")),
    ]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert _gate_is_clean(payload) is True, path.name
