import json
from pathlib import Path

from src.transform.rais_value_semantics import (
    normalize_value,
    validate_value_semantics,
)


CONTRACT = """version: 2
dataset: rais_vinculos
active_3112:
  active_values: ["1"]
  inactive_values: ["0"]
  reject_unknown_values: true
  reject_blank_values: true
"""


def _write_profile(
    path: Path,
    *,
    active_values: list[str],
    active_blank: int = 0,
    years: list[str] | None = None,
) -> None:
    path.write_text(
        json.dumps(
            {
                "year": 2025,
                "profile_complete": True,
                "aggregate": {
                    "active_3112": {
                        "blank": active_blank,
                        "observed_values": active_values,
                    },
                    "year": {
                        "blank": 0,
                        "observed_values": years or ["2025"],
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def test_value_semantics_accepts_observed_2025_codes(tmp_path: Path):
    profile = tmp_path / "profile.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "values.json"

    _write_profile(profile, active_values=["0", "1"])
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_value_semantics(
        profile,
        contract,
        destination,
        year=2025,
    )

    assert payload["value_semantics_valid"] is True
    assert payload["silver_transform_ready"] is True
    assert payload["publication_ready"] is False
    assert payload["active_3112"]["active_observed"] == ["1"]
    assert payload["active_3112"]["inactive_observed"] == ["0"]
    assert payload["active_3112"]["unknown_values"] == []


def test_value_semantics_blocks_unknown_code(tmp_path: Path):
    profile = tmp_path / "profile.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "values.json"

    _write_profile(profile, active_values=["0", "1", "9"])
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_value_semantics(
        profile,
        contract,
        destination,
        year=2025,
    )

    assert payload["value_semantics_valid"] is False
    assert payload["silver_transform_ready"] is False
    assert payload["active_3112"]["unknown_values"] == ["9"]


def test_value_semantics_blocks_blank_active_status(tmp_path: Path):
    profile = tmp_path / "profile.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "values.json"

    _write_profile(
        profile,
        active_values=["0", "1"],
        active_blank=1,
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_value_semantics(
        profile,
        contract,
        destination,
        year=2025,
    )

    assert payload["silver_transform_ready"] is False


def test_value_semantics_blocks_wrong_year(tmp_path: Path):
    profile = tmp_path / "profile.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "values.json"

    _write_profile(
        profile,
        active_values=["0", "1"],
        years=["2024"],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_value_semantics(
        profile,
        contract,
        destination,
        year=2025,
    )

    assert payload["year_check"]["valid"] is False
    assert payload["silver_transform_ready"] is False
