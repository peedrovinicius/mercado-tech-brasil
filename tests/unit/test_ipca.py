from decimal import Decimal
from pathlib import Path

from src.reference.ipca import (
    build_sidra_url,
    correct_to_base,
    load_ipca_cache,
    save_ipca_cache,
)


def test_sidra_url_uses_ipca_number_index_series():
    url = build_sidra_url(["202607", "202608"])

    assert "/t/1737/" in url
    assert "/v/2266/" in url
    assert "202607,202608" in url


def test_correct_to_base_uses_index_ratio():
    value = correct_to_base(
        100,
        observation_index=100,
        base_index=125,
    )

    assert value == Decimal(125)


def test_ipca_cache_roundtrip(tmp_path: Path):
    destination = tmp_path / "ipca.json"
    save_ipca_cache(
        {
            "202607": Decimal("7300.1"),
            "202608": Decimal("7310.2"),
        },
        base_competence="202608",
        destination=destination,
    )

    payload = load_ipca_cache(destination)
    assert payload["base_competence"] == "202608"
    assert payload["indices"]["202607"] == "7300.1"
