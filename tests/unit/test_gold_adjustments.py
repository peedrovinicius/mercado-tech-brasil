import json
from pathlib import Path

import polars as pl

from src.gold.aggregate import build_gold


def test_gold_reconciles_for_exc_and_builds_municipality_and_trend(tmp_path: Path):
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"
    silver_dir.mkdir()

    base = silver_dir / "caged_tech_202607.parquet"
    pl.DataFrame(
        {
            "uf": ["CE", "CE", "CE"],
            "municipio_codigo_caged": ["230440", "230440", "230440"],
            "cbo_familia": ["2124", "2124", "2124"],
            "cbo_codigo": ["212405", "212405", "212405"],
            "saldo_movimentacao": [1, 1, -1],
            "salario_mensal": [3000.0, 5000.0, 4500.0],
            "indicador_trabalho_intermitente": ["0", "0", "0"],
        }
    ).write_parquet(base)

    pl.DataFrame(
        {
            "uf": ["CE"],
            "municipio_codigo_caged": ["230440"],
            "cbo_familia": ["2124"],
            "cbo_codigo": ["212405"],
            "saldo_movimentacao": [1],
            "salario_mensal": [7000.0],
            "indicador_trabalho_intermitente": ["0"],
            "admissions_delta": [1],
            "dismissals_delta": [0],
            "balance_delta": [1],
            "effective_competence": ["202607"],
            "adjustment_kind": ["FOR"],
        }
    ).write_parquet(silver_dir / "caged_tech_for_202608.parquet")

    pl.DataFrame(
        {
            "uf": ["CE"],
            "municipio_codigo_caged": ["230440"],
            "cbo_familia": ["2124"],
            "cbo_codigo": ["212405"],
            "saldo_movimentacao": [1],
            "salario_mensal": [3000.0],
            "indicador_trabalho_intermitente": ["0"],
            "admissions_delta": [-1],
            "dismissals_delta": [0],
            "balance_delta": [-1],
            "effective_competence": ["202607"],
            "adjustment_kind": ["EXC"],
        }
    ).write_parquet(silver_dir / "caged_tech_exc_202609.parquet")

    municipality_cache = tmp_path / "municipalities.json"
    municipality_cache.write_text(
        json.dumps(
            {
                "municipalities": {
                    "230440": {
                        "municipio_codigo_ibge": "2304400",
                        "municipio_nome": "Fortaleza",
                        "uf": "CE",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    _, overview_path = build_gold(
        base,
        yearmonth="202607",
        gold_dir=gold_dir,
        municipalities_cache_path=municipality_cache,
    )

    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    municipalities = json.loads(
        (gold_dir / "by-municipality-202607.json").read_text(encoding="utf-8")
    )
    trend = json.loads((gold_dir / "trend.json").read_text(encoding="utf-8"))

    assert overview["admissions"] == 2
    assert overview["dismissals"] == 1
    assert overview["balance"] == 1
    assert overview["salary_mean_admissions"] == 6000.0
    assert overview["salary_median_admissions"] == 6000.0
    assert municipalities["items"][0]["municipio_nome"] == "Fortaleza"
    assert trend["items"][0]["competence"] == "202607"
