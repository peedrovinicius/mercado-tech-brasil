import json
from pathlib import Path

from src.transform.rais_value_semantics import validate_value_semantics

CONTRACT = """version: 3
dataset: rais_vinculos
active_3112:
  active_values: ["1"]
  inactive_values: ["0"]
  reject_unknown_values: true
  reject_blank_values: true
abandoned_link:
  eligible_values: ["0"]
  excluded_values: ["1"]
  reject_unknown_values: true
  reject_blank_values: true
"""


def _write_profile(
    path: Path,
    *,
    active_values: list[str],
    abandoned_values: list[str] | None = None,
    abandoned_blank: int = 0,
    years: list[str] | None = None,
) -> None:
    path.write_text(
        json.dumps(
            {
                "year": 2025,
                "profile_complete": True,
                "aggregate": {
                    "active_3112": {
                        "blank": 0,
                        "observed_values": active_values,
                    },
                    "abandoned_link": {
                        "blank": abandoned_blank,
                        "observed_values": abandoned_values or ["0", "1"],
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


def test_value_semantics_accepts_stock_codes(tmp_path: Path):
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

    assert payload["silver_transform_ready"] is True
    assert payload["active_3112"]["active_observed"] == ["1"]
    assert payload["abandoned_link"]["eligible_observed"] == ["0"]
    assert payload["abandoned_link"]["excluded_observed"] == ["1"]


def test_value_semantics_blocks_unknown_abandoned_code(tmp_path: Path):
    profile = tmp_path / "profile.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "values.json"

    _write_profile(
        profile,
        active_values=["0", "1"],
        abandoned_values=["0", "1", "9"],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_value_semantics(
        profile,
        contract,
        destination,
        year=2025,
    )

    assert payload["silver_transform_ready"] is False
    assert payload["abandoned_link"]["unknown_values"] == ["9"]


def test_value_semantics_blocks_blank_abandoned_status(tmp_path: Path):
    profile = tmp_path / "profile.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "values.json"

    _write_profile(
        profile,
        active_values=["0", "1"],
        abandoned_blank=1,
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
