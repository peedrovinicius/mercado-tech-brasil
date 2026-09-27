import json
from pathlib import Path

from src.validation.rais_regional_reconciliation import (
    evaluate_rais_regional_reconciliation,
    write_rais_regional_reconciliation,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_regional_reconciliation_requires_exact_group_totals(tmp_path: Path):
    parts = tmp_path / "parts"
    refs = tmp_path / "refs.json"

    _write(
        refs,
        {
            "2025": {
                "source": "MTE",
                "source_url": "https://example.invalid/rais.pdf",
                "source_page": 19,
                "national_active_links": 30,
                "groups": {
                    "A.7z": {
                        "label": "A",
                        "expected_stock": 10,
                    },
                    "B.7z": {
                        "label": "B",
                        "expected_stock": 20,
                    },
                },
            }
        },
    )

    _write(
        parts / "a" / "part-summary.json",
        {
            "year": 2025,
            "archive": "A.7z",
            "rows_active_source": 12,
            "rows_abandoned_source": 2,
            "rows_stock_eligible_source": 10,
            "rows_unknown_abandoned_source": 0,
            "rows_unknown_status_source": 0,
            "rows_rejected": 0,
        },
    )
    _write(
        parts / "b" / "part-summary.json",
        {
            "year": 2025,
            "archive": "B.7z",
            "rows_active_source": 23,
            "rows_abandoned_source": 3,
            "rows_stock_eligible_source": 20,
            "rows_unknown_abandoned_source": 0,
            "rows_unknown_status_source": 0,
            "rows_rejected": 0,
        },
    )

    result = evaluate_rais_regional_reconciliation(
        year=2025,
        parts_root=parts,
        reference_path=refs,
    )

    assert result.regional_reconciled is True
    assert result.observed_national_stock == 30
    assert result.difference == 0
    assert all(item.matched for item in result.groups)


def test_regional_reconciliation_blocks_one_link_difference(tmp_path: Path):
    parts = tmp_path / "parts"
    refs = tmp_path / "refs.json"

    _write(
        refs,
        {
            "2025": {
                "national_active_links": 10,
                "groups": {
                    "A.7z": {
                        "label": "A",
                        "expected_stock": 10,
                    }
                },
            }
        },
    )
    _write(
        parts / "a" / "part-summary.json",
        {
            "year": 2025,
            "archive": "A.7z",
            "rows_active_source": 11,
            "rows_abandoned_source": 2,
            "rows_stock_eligible_source": 9,
            "rows_unknown_abandoned_source": 0,
            "rows_unknown_status_source": 0,
            "rows_rejected": 0,
        },
    )

    result = evaluate_rais_regional_reconciliation(
        year=2025,
        parts_root=parts,
        reference_path=refs,
    )

    assert result.regional_reconciled is False
    assert result.groups[0].difference == -1


def test_write_regional_reconciliation(tmp_path: Path):
    parts = tmp_path / "parts"
    refs = tmp_path / "refs.json"
    destination = tmp_path / "regional.json"

    _write(
        refs,
        {
            "2025": {
                "national_active_links": 1,
                "groups": {
                    "A.7z": {
                        "label": "A",
                        "expected_stock": 1,
                    }
                },
            }
        },
    )
    _write(
        parts / "a" / "part-summary.json",
        {
            "year": 2025,
            "archive": "A.7z",
            "rows_active_source": 1,
            "rows_abandoned_source": 0,
            "rows_stock_eligible_source": 1,
            "rows_unknown_abandoned_source": 0,
            "rows_unknown_status_source": 0,
            "rows_rejected": 0,
        },
    )

    result = evaluate_rais_regional_reconciliation(
        year=2025,
        parts_root=parts,
        reference_path=refs,
    )
    write_rais_regional_reconciliation(result, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["regional_reconciled"] is True
    assert payload["groups"][0]["matched"] is True
