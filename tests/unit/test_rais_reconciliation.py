import json
from pathlib import Path

from src.validation.rais_reconciliation import (
    evaluate_rais_reconciliation,
    write_rais_reconciliation,
)


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _quality(stock: int, *, raw: int | None = None) -> dict:
    raw_active = raw if raw is not None else stock
    abandoned = raw_active - stock
    return {
        "year": 2025,
        "rows_active_source": raw_active,
        "rows_abandoned_source": abandoned,
        "rows_stock_eligible_source": stock,
        "rows_unknown_abandoned_source": 0,
        "rows_inactive_source": 100,
        "rows_unknown_status_source": 0,
        "rows_year_mismatch_source": 0,
        "source_partition_complete": True,
        "stock_partition_complete": True,
        "rows_tech": 500000,
    }


def _reference() -> dict:
    return {
        "2025": {
            "source": "RAIS 2025 / MTE",
            "source_url": "https://example.invalid/official",
            "active_links": 59970945,
        }
    }


def test_reconciliation_uses_qualified_stock_not_raw_active(tmp_path: Path):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"
    _write(quality, _quality(59970945, raw=60691770))
    _write(reference, _reference())

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )

    assert result.reconciled is True
    assert result.observed_active == 59970945
    assert result.raw_active_source == 60691770
    assert result.abandoned_active_source == 720825
    assert result.difference == 0


def test_reconciliation_blocks_one_link_difference(tmp_path: Path):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"
    _write(quality, _quality(59970944, raw=60691769))
    _write(reference, _reference())

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )

    assert result.reconciled is False
    assert result.difference == -1


def test_reconciliation_blocks_unknown_abandoned_or_partition_error(
    tmp_path: Path,
):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"
    payload = _quality(59970945, raw=60691770)
    payload["rows_unknown_abandoned_source"] = 1
    payload["stock_partition_complete"] = False
    _write(quality, payload)
    _write(reference, _reference())

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )

    assert result.reconciled is False
    assert result.gold_ready is False


def test_write_reconciliation_keeps_publication_blocked(tmp_path: Path):
    quality = tmp_path / "quality.json"
    reference = tmp_path / "reference.json"
    destination = tmp_path / "reconciliation.json"
    _write(quality, _quality(59970945, raw=60691770))
    _write(reference, _reference())

    result = evaluate_rais_reconciliation(
        year=2025,
        quality_path=quality,
        reference_path=reference,
    )
    write_rais_reconciliation(result, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["gold_ready"] is True
    assert payload["publication_ready"] is False
