import json
from pathlib import Path

import polars as pl

from src.gold.rais_municipalities import build_rais_municipality_gold


def test_build_rais_municipality_gold(tmp_path: Path):
    silver = tmp_path / "silver.parquet"
    validation = tmp_path / "validation.json"
    gold = tmp_path / "gold"

    pl.DataFrame(
        {
            "municipio_codigo": [
                "230440",
                "230440",
                "355030",
                "999999",
            ],
            "uf": ["CE", "CE", "SP", "NI"],
        }
    ).write_parquet(silver)
    validation.write_text(
        json.dumps(
            {
                "year": 2025,
                "municipality_ready": True,
            }
        ),
        encoding="utf-8",
    )

    mapping = {
        "230440": {
            "municipio_codigo_ibge": "2304400",
            "municipio_nome": "Fortaleza",
            "uf": "CE",
        },
        "355030": {
            "municipio_codigo_ibge": "3550308",
            "municipio_nome": "São Paulo",
            "uf": "SP",
        },
    }

    destination = build_rais_municipality_gold(
        year=2025,
        silver_path=silver,
        validation_path=validation,
        gold_dir=gold,
        municipalities=mapping,
    )

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["active_stock_tech"] == 4
    assert payload["municipality_count"] == 3
    assert sum(item["active_stock"] for item in payload["items"]) == 4
    assert payload["items"][0]["municipio_nome"] == "Fortaleza"

    residual = next(
        item
        for item in payload["items"]
        if item["municipio_codigo_rais"] == "999999"
    )
    assert residual["municipio_codigo_ibge"] is None
    assert residual["municipio_nome"] == "Não identificado"
    assert residual["uf"] == "NI"


def test_rais_municipality_gold_requires_validated_dimension(tmp_path: Path):
    silver = tmp_path / "silver.parquet"
    validation = tmp_path / "validation.json"

    pl.DataFrame(
        {"municipio_codigo": ["230440"], "uf": ["CE"]}
    ).write_parquet(silver)
    validation.write_text(
        json.dumps(
            {"year": 2025, "municipality_ready": False}
        ),
        encoding="utf-8",
    )

    try:
        build_rais_municipality_gold(
            year=2025,
            silver_path=silver,
            validation_path=validation,
            gold_dir=tmp_path / "gold",
            municipalities={},
        )
    except ValueError as exc:
        assert "validada" in str(exc)
    else:
        raise AssertionError("Gold municipal deveria permanecer bloqueado.")
