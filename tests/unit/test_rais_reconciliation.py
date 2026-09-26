import json
from pathlib import Path

from src.validation.rais_reconciliation import (
    evaluate_rais_reconciliation,
    write_rais_reconciliation,
)


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_rais_reconciliation_passes_only_on_exact_official_total(tmp_path: Path):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"

    _write(
        quality,
        {
            "year": 2025,
            "rows_active_source": 59970945,
            "rows_inactive_source": 100,
            "rows_unknown_status_source": 0,
            "rows_year_mismatch_source": 0,
            "rows_read": 59971045,
            "source_partition_complete": True,
            "rows_tech": 500000,
        },
    )
    _write(
        reference,
        {
            "2025": {
                "source": "RAIS 2025 / MTE",
                "source_url": "https://example.invalid/official",
                "active_links": 59970945,
            }
        },
    )

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )

    assert result.reconciled is True
    assert result.gold_ready is True
    assert result.publication_ready is False
    assert result.difference == 0


def test_rais_reconciliation_blocks_one_link_difference(tmp_path: Path):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"

    _write(
        quality,
        {
            "year": 2025,
            "rows_active_source": 59970944,
            "rows_unknown_status_source": 0,
            "rows_year_mismatch_source": 0,
            "source_partition_complete": True,
            "rows_tech": 500000,
        },
    )
    _write(
        reference,
        {
            "2025": {
                "source": "RAIS 2025 / MTE",
                "source_url": "https://example.invalid/official",
                "active_links": 59970945,
            }
        },
    )

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )

    assert result.reconciled is False
    assert result.gold_ready is False
    assert result.difference == -1


def test_rais_reconciliation_blocks_unknown_status_or_partition_error(
    tmp_path: Path,
):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"

    _write(
        quality,
        {
            "year": 2025,
            "rows_active_source": 59970945,
            "rows_unknown_status_source": 1,
            "rows_year_mismatch_source": 0,
            "source_partition_complete": False,
            "rows_tech": 500000,
        },
    )
    _write(
        reference,
        {
            "2025": {
                "source": "RAIS 2025 / MTE",
                "source_url": "https://example.invalid/official",
                "active_links": 59970945,
            }
        },
    )

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )

    assert result.reconciled is False
    assert result.gold_ready is False


def test_write_rais_reconciliation_keeps_publication_blocked(tmp_path: Path):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"
    destination = tmp_path / "reconciliation.json"

    _write(
        quality,
        {
            "year": 2025,
            "rows_active_source": 10,
            "rows_unknown_status_source": 0,
            "rows_year_mismatch_source": 0,
            "source_partition_complete": True,
            "rows_tech": 2,
        },
    )
    _write(
        reference,
        {
            "2025": {
                "source": "RAIS 2025 / MTE",
                "source_url": "https://example.invalid/official",
                "active_links": 10,
            }
        },
    )

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )
    write_rais_reconciliation(result, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["gold_ready"] is True
    assert payload["publication_ready"] is False
