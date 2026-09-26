import json
from pathlib import Path

from src.reference.population import (
    build_population_url,
    load_population_cache,
    parse_population_payload,
    save_population_cache,
)


def test_build_population_url_uses_sidra_6579():
    url = build_population_url(2026)

    assert "/6579/periodos/2026/variaveis/9324" in url
    assert "localidades=N6[all]" in url


def test_parse_population_payload_reads_municipal_series():
    payload = [
        {
            "id": "9324",
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {
                            "localidade": {
                                "id": "2304400",
                                "nome": "Fortaleza - CE",
                            },
                            "serie": {"2026": "2500000"},
                        },
                        {
                            "localidade": {
                                "id": "3550308",
                                "nome": "São Paulo - SP",
                            },
                            "serie": {"2026": "12000000"},
                        },
                    ],
                }
            ],
        }
    ]

    result = parse_population_payload(payload, year=2026)

    assert result == {
        "2304400": 2500000,
        "3550308": 12000000,
    }


def test_population_cache_roundtrip(tmp_path: Path):
    destination = tmp_path / "population.json"
    populations = {
        f"{1000000 + index:07d}": 1000 + index
        for index in range(5001)
    }

    save_population_cache(
        populations,
        year=2026,
        destination=destination,
    )
    loaded = load_population_cache(destination)

    assert loaded["reference_year"] == 2026
    assert loaded["reference_date"] == "2026-07-01"
    assert loaded["table"] == "6579"
    assert loaded["variable"] == "9324"
    assert len(loaded["municipalities"]) == 5001

    raw = json.loads(destination.read_text(encoding="utf-8"))
    assert raw["source"] == "IBGE SIDRA"
