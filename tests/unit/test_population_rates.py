import json
from pathlib import Path

from src.gold.aggregate import enrich_municipality_items


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_municipality_population_rates_are_derived_from_ibge_code(
    tmp_path: Path,
):
    municipalities = tmp_path / "municipalities.json"
    population = tmp_path / "population.json"

    _write_json(
        municipalities,
        {
            "municipalities": {
                "230440": {
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                }
            }
        },
    )
    _write_json(
        population,
        {
            "source": "IBGE SIDRA",
            "table": "6579",
            "variable": "9324",
            "reference_year": 2026,
            "reference_date": "2026-07-01",
            "municipalities": {"2304400": 2500000},
        },
    )

    items = [
        {
            "municipio_codigo_caged": "230440",
            "admissions": 100,
            "dismissals": 80,
            "balance": 20,
        },
        {
            "municipio_codigo_caged": "999999",
            "admissions": 10,
            "dismissals": 8,
            "balance": 2,
        },
    ]

    enriched = enrich_municipality_items(
        items,
        municipalities,
        population,
    )

    fortaleza = enriched[0]
    assert fortaleza["population_estimate"] == 2500000
    assert fortaleza["population_reference_year"] == 2026
    assert fortaleza["admissions_per_100k"] == 4.0
    assert fortaleza["dismissals_per_100k"] == 3.2
    assert fortaleza["balance_per_100k"] == 0.8

    residual = enriched[1]
    assert residual["municipio_nome"] == "Não identificado"
    assert residual["population_estimate"] is None
    assert residual["admissions_per_100k"] is None
