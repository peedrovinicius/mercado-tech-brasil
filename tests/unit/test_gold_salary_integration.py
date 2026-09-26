import json
from pathlib import Path

import polars as pl

from src.gold.aggregate import build_gold


def test_gold_uses_official_salary_eligibility_rules(tmp_path: Path):
    silver = tmp_path / "silver.parquet"
    gold_dir = tmp_path / "gold"

    pl.DataFrame(
        {
            "uf": ["CE", "CE", "CE", "CE", "CE"],
            "cbo_familia": ["2124"] * 5,
            "cbo_codigo": ["212405"] * 5,
            "saldo_movimentacao": [1, 1, 1, 1, -1],
            "salario_mensal": [1000.0, 5000.0, 400.0, 8000.0, 9000.0],
            "indicador_trabalho_intermitente": ["0", "0", "0", "1", "0"],
        }
    ).write_parquet(silver)

    _, overview_path = build_gold(
        silver,
        yearmonth="202607",
        gold_dir=gold_dir,
    )
    overview = json.loads(overview_path.read_text(encoding="utf-8"))

    assert overview["admissions"] == 4
    assert overview["dismissals"] == 1
    assert overview["salary_eligible_admissions"] == 2
    assert overview["salary_excluded_admissions"] == 2
    assert overview["salary_mean_admissions"] == 3000.0
    assert overview["salary_median_admissions"] == 3000.0
    assert overview["salary_methodology"]["minimum_salary_brl"] == 486.30
    assert overview["salary_methodology"]["maximum_salary_brl"] == 243150.00
