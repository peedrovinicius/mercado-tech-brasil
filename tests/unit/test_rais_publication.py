import json
from pathlib import Path

from src.api.publication import (
    latest_published_rais_year,
    published_rais_json_path,
    published_rais_years,
    rais_publication_registry,
)


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_rais_publication_helpers_only_expose_publishable_years(tmp_path: Path):
    _write(
        tmp_path / "rais-publication-gate-2024.json",
        {
            "year": 2024,
            "automatic_checks_passed": True,
            "manual_approval_valid": False,
            "publishable": False,
            "release_sha256": "a" * 64,
        },
    )
    _write(
        tmp_path / "rais-publication-gate-2025.json",
        {
            "year": 2025,
            "automatic_checks_passed": True,
            "manual_approval_valid": True,
            "publishable": True,
            "release_sha256": "b" * 64,
        },
    )
    _write(
        tmp_path / "rais-overview-2025.json",
        {"year": 2025, "active_stock_tech": 10},
    )

    assert published_rais_years(tmp_path) == [2025]
    assert latest_published_rais_year(tmp_path) == 2025
    assert published_rais_json_path(
        tmp_path,
        prefix="rais-overview",
        year=2025,
    ) == tmp_path / "rais-overview-2025.json"
    assert published_rais_json_path(
        tmp_path,
        prefix="rais-overview",
        year=2024,
    ) is None

    registry = rais_publication_registry(tmp_path)
    assert [item["year"] for item in registry] == [2024, 2025]
    assert registry[0]["publishable"] is False
    assert registry[1]["publishable"] is True
