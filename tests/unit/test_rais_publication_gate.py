import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.validation.rais_publication_gate import (
    approve_rais_release,
    evaluate_rais_publication_gate,
    write_rais_publication_gate,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _prepare_release(base: Path) -> tuple[Path, Path, Path, Path]:
    bronze = base / "bronze"
    silver = base / "silver"
    gold = base / "gold"
    approvals = base / "config" / "rais_approvals.json"

    _write_json(
        bronze / "rais" / "2025" / "archives" / "download-manifest.json",
        {
            "files": [
                {"sha256": "a" * 64},
                {"sha256": "b" * 64},
            ]
        },
    )
    _write_json(
        silver / "rais_reconciliation_2025.json",
        {
            "year": 2025,
            "expected_active": 1000,
            "observed_active": 1000,
            "difference": 0,
            "reconciled": True,
            "gold_ready": True,
            "publication_ready": False,
        },
    )
    _write_json(
        gold / "rais-overview-2025.json",
        {
            "year": 2025,
            "active_stock_tech": 4,
            "active_stock_national_reference": 1000,
            "publication_ready": False,
        },
    )
    _write_json(
        gold / "rais-by-uf-2025.json",
        {
            "year": 2025,
            "items": [
                {"uf": "CE", "active_stock": 2},
                {"uf": "SP", "active_stock": 2},
            ],
            "publication_ready": False,
        },
    )
    _write_json(
        gold / "rais-by-cbo-family-2025.json",
        {
            "year": 2025,
            "items": [
                {"cbo_familia": "2124", "active_stock": 3},
                {"cbo_familia": "3171", "active_stock": 1},
            ],
            "publication_ready": False,
        },
    )

    gold.mkdir(parents=True, exist_ok=True)
    table = pa.table({"active_stock": [2, 1, 1]})
    pq.write_table(table, gold / "rais-market-2025.parquet")

    return bronze, silver, gold, approvals


def test_rais_gate_requires_manual_approval(tmp_path: Path):
    bronze, silver, gold, approvals = _prepare_release(tmp_path)

    result = evaluate_rais_publication_gate(
        year=2025,
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is True
    assert result.manual_approval_valid is False
    assert result.publishable is False
    assert len(result.release_sha256 or "") == 64


def test_rais_gate_becomes_publishable_after_matching_approval(tmp_path: Path):
    bronze, silver, gold, approvals = _prepare_release(tmp_path)

    approval = approve_rais_release(
        year=2025,
        reviewer="reviewer",
        notes="Metodologia e agregados revisados.",
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )
    assert len(approval["release_sha256"]) == 64

    result = evaluate_rais_publication_gate(
        year=2025,
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is True
    assert result.manual_approval_valid is True
    assert result.publishable is True


def test_rais_approval_is_invalidated_when_gold_changes(tmp_path: Path):
    bronze, silver, gold, approvals = _prepare_release(tmp_path)

    approve_rais_release(
        year=2025,
        reviewer="reviewer",
        notes="Revisado.",
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )

    overview = gold / "rais-overview-2025.json"
    payload = json.loads(overview.read_text(encoding="utf-8"))
    payload["extra"] = "mudança"
    overview.write_text(json.dumps(payload), encoding="utf-8")

    result = evaluate_rais_publication_gate(
        year=2025,
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is True
    assert result.manual_approval_valid is False
    assert result.publishable is False


def test_rais_gate_blocks_aggregate_mismatch(tmp_path: Path):
    bronze, silver, gold, approvals = _prepare_release(tmp_path)

    payload = json.loads(
        (gold / "rais-by-uf-2025.json").read_text(encoding="utf-8")
    )
    payload["items"][0]["active_stock"] = 3
    _write_json(gold / "rais-by-uf-2025.json", payload)

    result = evaluate_rais_publication_gate(
        year=2025,
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is False
    assert result.publishable is False


def test_write_rais_gate_report(tmp_path: Path):
    bronze, silver, gold, approvals = _prepare_release(tmp_path)
    destination = gold / "rais-publication-gate-2025.json"

    result = evaluate_rais_publication_gate(
        year=2025,
        bronze_dir=bronze,
        silver_dir=silver,
        gold_dir=gold,
        approvals_path=approvals,
    )
    write_rais_publication_gate(result, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["year"] == 2025
    assert payload["publishable"] is False
    assert payload["checks"]
