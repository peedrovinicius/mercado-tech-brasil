import json
from datetime import date
from pathlib import Path

import pytest

from src.validation.incremental_release import (
    evaluate_next_competence,
    validate_requested_competence,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _reference(published_at: str, admissions: int = 120, dismissals: int = 100) -> dict:
    return {
        "source": "Ministério do Trabalho e Emprego",
        "source_url": "https://example.test/mte",
        "published_at": published_at,
        "reference_kind": "published_monthly_mov",
        "admissoes": admissions,
        "desligamentos": dismissals,
        "saldo": admissions - dismissals,
    }


def _published_gate(gold: Path, competence: str) -> None:
    _write_json(
        gold / f"publication-gate-{competence}.json",
        {
            "competence": competence,
            "automatic_checks_passed": True,
            "manual_approval_valid": True,
            "publishable": True,
            "source_sha256": "abc123",
        },
    )


def test_next_competence_requires_continuous_official_reference(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202412")
    _write_json(
        reference_path,
        {
            "202412": _reference("2025-01-10"),
            "202501": _reference("2025-02-10"),
        },
    )

    result = evaluate_next_competence(
        reference_path=reference_path,
        gold_path=gold,
        today=date(2025, 2, 11),
    )

    assert result.ready is True
    assert result.reason == "ready"
    assert result.latest_published == "202412"
    assert result.next_expected == "202501"
    assert result.candidate == "202501"


def test_next_competence_blocks_without_official_reference(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202412")
    _write_json(reference_path, {"202412": _reference("2025-01-10")})

    result = evaluate_next_competence(
        reference_path=reference_path,
        gold_path=gold,
        today=date(2025, 2, 11),
    )

    assert result.ready is False
    assert result.reason == "official_reference_not_registered"
    assert result.next_expected == "202501"
    assert result.candidate is None


def test_next_competence_blocks_reference_gap(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202411")
    _write_json(
        reference_path,
        {
            "202411": _reference("2024-12-10"),
            "202501": _reference("2025-02-10"),
        },
    )

    result = evaluate_next_competence(
        reference_path=reference_path,
        gold_path=gold,
        today=date(2025, 2, 11),
    )

    assert result.ready is False
    assert result.reason == "reference_gap"
    assert result.next_expected == "202412"


def test_next_competence_blocks_future_publication_date(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202412")
    _write_json(
        reference_path,
        {
            "202412": _reference("2025-01-10"),
            "202501": _reference("2025-02-20"),
        },
    )

    result = evaluate_next_competence(
        reference_path=reference_path,
        gold_path=gold,
        today=date(2025, 2, 11),
    )

    assert result.ready is False
    assert result.reason == "reference_not_effective_yet"
    assert result.candidate is None


def test_next_competence_rejects_inconsistent_reference(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202412")
    invalid = _reference("2025-02-10")
    invalid["saldo"] = 999
    _write_json(
        reference_path,
        {
            "202412": _reference("2025-01-10"),
            "202501": invalid,
        },
    )

    with pytest.raises(ValueError, match="aritmeticamente inconsistente"):
        evaluate_next_competence(
            reference_path=reference_path,
            gold_path=gold,
            today=date(2025, 2, 11),
        )


def test_requested_competence_cannot_skip_expected_month(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202412")
    _write_json(
        reference_path,
        {
            "202412": _reference("2025-01-10"),
            "202501": _reference("2025-02-10"),
            "202502": _reference("2025-03-10"),
        },
    )

    with pytest.raises(ValueError, match="não elegível"):
        validate_requested_competence(
            "202502",
            reference_path=reference_path,
            gold_path=gold,
            today=date(2025, 3, 11),
        )


def test_published_competence_can_be_explicitly_reaudited(tmp_path: Path):
    reference_path = tmp_path / "reference.json"
    gold = tmp_path / "gold"
    _published_gate(gold, "202412")
    _write_json(
        reference_path,
        {"202412": _reference("2025-01-10")},
    )

    result = validate_requested_competence(
        "202412",
        reference_path=reference_path,
        gold_path=gold,
        allow_published=True,
        today=date(2025, 2, 11),
    )

    assert result.ready is True
    assert result.reason == "published_reaudit"
    assert result.candidate == "202412"
