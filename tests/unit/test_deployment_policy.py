import json
from pathlib import Path

from src.validation.deployment_policy import evaluate_deployment_changes


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _monthly_gate(*, publishable: bool = True) -> dict:
    return {
        "competence": "202607",
        "automatic_checks_passed": publishable,
        "manual_approval_valid": publishable,
        "publishable": publishable,
        "checks": [
            {
                "id": "manual_methodology_approval",
                "passed": publishable,
                "blocking": True,
            }
        ],
    }


def _rais_gate(*, publishable: bool = True) -> dict:
    return {
        "year": 2025,
        "automatic_checks_passed": publishable,
        "manual_approval_valid": publishable,
        "publishable": publishable,
        "checks": [
            {
                "id": "manual_methodology_approval",
                "passed": publishable,
                "blocking": True,
            }
        ],
    }


def test_policy_allows_code_only_change(tmp_path: Path):
    decision = evaluate_deployment_changes(
        changed_paths=["src/api/main.py", "frontend/src/App.tsx"],
        gold_dir=tmp_path,
    )

    assert decision.eligible is True
    assert decision.monthly_competencies == ()
    assert decision.rais_years == ()


def test_policy_allows_published_monthly_release(tmp_path: Path):
    _write(
        tmp_path / "publication-gate-202607.json",
        _monthly_gate(),
    )

    decision = evaluate_deployment_changes(
        changed_paths=[
            "data/gold/overview-202607.json",
            "data/gold/publication-gate-202607.json",
        ],
        gold_dir=tmp_path,
    )

    assert decision.eligible is True
    assert decision.monthly_competencies == ("202607",)


def test_policy_blocks_monthly_release_before_approval(tmp_path: Path):
    _write(
        tmp_path / "publication-gate-202607.json",
        _monthly_gate(publishable=False),
    )

    decision = evaluate_deployment_changes(
        changed_paths=["data/gold/overview-202607.json"],
        gold_dir=tmp_path,
    )

    assert decision.eligible is False
    assert "ainda não está publicável" in decision.reasons[0]


def test_policy_blocks_monthly_release_without_gate(tmp_path: Path):
    decision = evaluate_deployment_changes(
        changed_paths=["data/gold/overview-202607.json"],
        gold_dir=tmp_path,
    )

    assert decision.eligible is False
    assert "gate mensal ausente" in decision.reasons[0]


def test_policy_allows_published_rais_release(tmp_path: Path):
    _write(
        tmp_path / "rais-publication-gate-2025.json",
        _rais_gate(),
    )

    decision = evaluate_deployment_changes(
        changed_paths=[
            "data/gold/rais-overview-2025.json",
            "data/gold/rais-publication-gate-2025.json",
        ],
        gold_dir=tmp_path,
    )

    assert decision.eligible is True
    assert decision.rais_years == (2025,)


def test_policy_blocks_rais_before_approval(tmp_path: Path):
    _write(
        tmp_path / "rais-publication-gate-2025.json",
        _rais_gate(publishable=False),
    )

    decision = evaluate_deployment_changes(
        changed_paths=["data/gold/rais-overview-2025.json"],
        gold_dir=tmp_path,
    )

    assert decision.eligible is False
