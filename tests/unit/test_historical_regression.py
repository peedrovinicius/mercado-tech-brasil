import json
from pathlib import Path

import polars as pl
import pytest

from src.validation.historical_regression import (
    apply_history_revision_package,
    evaluate_history_revisions,
    snapshot_published_history,
    write_history_snapshot,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _published_fixture(tmp_path: Path, competence: str = "202501"):
    gold = tmp_path / "gold"
    silver = tmp_path / "silver"
    package_root = tmp_path / "revisions"
    silver.mkdir()

    _write_json(
        gold / f"publication-gate-{competence}.json",
        {
            "competence": competence,
            "publishable": True,
        },
    )
    _write_json(
        gold / f"overview-{competence}.json",
        {
            "competence": competence,
            "admissions": 10,
            "dismissals": 8,
            "balance": 2,
            "salary_median_admissions_real": 4000.0,
        },
    )
    for prefix in ("by-uf", "by-occupation", "by-municipality"):
        _write_json(
            gold / f"{prefix}-{competence}.json",
            {"competence": competence, "items": []},
        )
    (gold / f"market-{competence}.parquet").write_bytes(b"baseline-market")

    baseline_path = tmp_path / "baseline.json"
    snapshot = snapshot_published_history(gold)
    write_history_snapshot(snapshot, baseline_path)
    return gold, silver, package_root, baseline_path


def _write_adjustment(
    silver: Path,
    *,
    ingest_competence: str,
    effective_competence: str,
) -> None:
    pl.DataFrame(
        {
            "effective_competence": [effective_competence],
        }
    ).write_parquet(
        silver / f"caged_tech_for_{ingest_competence}.parquet"
    )


def test_expected_historical_change_is_packaged(tmp_path: Path):
    gold, silver, package_root, baseline = _published_fixture(tmp_path)
    _write_adjustment(
        silver,
        ingest_competence="202502",
        effective_competence="202501",
    )

    _write_json(
        gold / "overview-202501.json",
        {
            "competence": "202501",
            "admissions": 11,
            "dismissals": 8,
            "balance": 3,
            "salary_median_admissions_real": 4100.0,
        },
    )

    result = evaluate_history_revisions(
        ingest_competence="202502",
        baseline_path=baseline,
        gold_dir=gold,
        silver_dir=silver,
        package_root=package_root,
    )

    assert result["passed"] is True
    assert result["changed_published_competencies"] == ["202501"]
    assert result["unexpected_changed_competencies"] == []
    assert len(result["packaged_files"]) == 5
    assert (
        package_root / "202502" / "gold" / "overview-202501.json"
    ).exists()


def test_unexplained_historical_change_is_blocked(tmp_path: Path):
    gold, silver, package_root, baseline = _published_fixture(tmp_path)
    _write_json(
        gold / "overview-202501.json",
        {
            "competence": "202501",
            "admissions": 12,
            "dismissals": 8,
            "balance": 4,
            "salary_median_admissions_real": 4000.0,
        },
    )

    result = evaluate_history_revisions(
        ingest_competence="202502",
        baseline_path=baseline,
        gold_dir=gold,
        silver_dir=silver,
        package_root=package_root,
    )

    assert result["passed"] is False
    assert result["unexpected_changed_competencies"] == ["202501"]
    assert result["packaged_files"] == []


def test_future_adjustment_competence_is_blocked(tmp_path: Path):
    gold, silver, package_root, baseline = _published_fixture(tmp_path)
    _write_adjustment(
        silver,
        ingest_competence="202502",
        effective_competence="202503",
    )

    result = evaluate_history_revisions(
        ingest_competence="202502",
        baseline_path=baseline,
        gold_dir=gold,
        silver_dir=silver,
        package_root=package_root,
    )

    assert result["passed"] is False
    assert result["future_adjustment_competencies"] == ["202503"]


def test_revision_package_requires_unchanged_published_baseline(tmp_path: Path):
    gold, silver, package_root, baseline = _published_fixture(tmp_path)
    original_overview = (gold / "overview-202501.json").read_text(
        encoding="utf-8"
    )
    _write_adjustment(
        silver,
        ingest_competence="202502",
        effective_competence="202501",
    )
    _write_json(
        gold / "overview-202501.json",
        {
            "competence": "202501",
            "admissions": 11,
            "dismissals": 8,
            "balance": 3,
            "salary_median_admissions_real": 4100.0,
        },
    )

    result = evaluate_history_revisions(
        ingest_competence="202502",
        baseline_path=baseline,
        gold_dir=gold,
        silver_dir=silver,
        package_root=package_root,
    )
    assert result["passed"] is True

    (gold / "overview-202501.json").write_text(
        original_overview,
        encoding="utf-8",
    )
    applied = apply_history_revision_package(
        ingest_competence="202502",
        gold_dir=gold,
        package_root=package_root,
    )
    assert len(applied) == 5
    assert json.loads(
        (gold / "overview-202501.json").read_text(encoding="utf-8")
    )["admissions"] == 11

    (gold / "overview-202501.json").write_text(
        original_overview,
        encoding="utf-8",
    )
    _write_json(
        gold / "overview-202501.json",
        {
            "competence": "202501",
            "admissions": 99,
            "dismissals": 90,
            "balance": 9,
        },
    )

    with pytest.raises(RuntimeError, match="Baseline publicado mudou"):
        apply_history_revision_package(
            ingest_competence="202502",
            gold_dir=gold,
            package_root=package_root,
        )
