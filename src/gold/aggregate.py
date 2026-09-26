from __future__ import annotations

import json
from pathlib import Path

from src.methodology.salary import add_salary_eligibility, methodology_for_competence


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_gold(
    silver_path: Path,
    *,
    yearmonth: str,
    gold_dir: Path,
) -> tuple[Path, Path]:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError(
            "Polars não está instalado. Execute pip install -e ."
        ) from exc

    data = pl.read_parquet(silver_path)
    data = add_salary_eligibility(data, yearmonth=yearmonth)
    salary_methodology = methodology_for_competence(yearmonth)

    admissions = data.filter(pl.col("saldo_movimentacao") == 1)
    dismissals = data.filter(pl.col("saldo_movimentacao") == -1)
    salary_admissions = data.filter(pl.col("salario_admissao_elegivel"))

    salary_expr = (
        pl.when(pl.col("salario_admissao_elegivel"))
        .then(pl.col("salario_mensal"))
        .otherwise(None)
    )

    summary = (
        data.group_by(["uf", "cbo_familia", "cbo_codigo"])
        .agg(
            (pl.col("saldo_movimentacao") == 1).sum().alias("admissoes"),
            (pl.col("saldo_movimentacao") == -1).sum().alias("desligamentos"),
            pl.col("saldo_movimentacao").sum().alias("saldo"),
            salary_expr.mean().alias("salario_medio_admissao"),
            salary_expr.median().alias("salario_mediano_admissao"),
            pl.col("salario_admissao_elegivel")
            .sum()
            .alias("admissoes_salario_elegivel"),
        )
        .with_columns(pl.lit(yearmonth).alias("competencia"))
        .sort(["uf", "cbo_familia", "cbo_codigo"])
    )

    gold_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = gold_dir / f"market-{yearmonth}.parquet"
    overview_path = gold_dir / f"overview-{yearmonth}.json"

    summary.write_parquet(parquet_path, compression="zstd")

    overview = {
        "competence": yearmonth,
        "scope": "recorte CBO de tecnologia versionado",
        "admissions": admissions.height,
        "dismissals": dismissals.height,
        "balance": int(data["saldo_movimentacao"].sum()) if data.height else 0,
        "salary_mean_admissions": (
            float(salary_admissions["salario_mensal"].mean())
            if salary_admissions.height
            else None
        ),
        "salary_median_admissions": (
            float(salary_admissions["salario_mensal"].median())
            if salary_admissions.height
            else None
        ),
        "salary_eligible_admissions": salary_admissions.height,
        "salary_excluded_admissions": admissions.height - salary_admissions.height,
        "salary_methodology": {
            "minimum_wage_brl": salary_methodology.minimum_wage_brl,
            "minimum_salary_brl": salary_methodology.minimum_salary_brl,
            "maximum_salary_brl": salary_methodology.maximum_salary_brl,
            "exclude_intermittent": True,
            "source": "MTE: Sumário Executivo Novo Caged",
        },
        "records_tech": data.height,
        "source": "Novo CAGED / MTE",
        "status": "generated_from_official_microdata",
    }
    _write_json(overview_path, overview)

    by_uf = (
        data.group_by("uf")
        .agg(
            (pl.col("saldo_movimentacao") == 1).sum().alias("admissions"),
            (pl.col("saldo_movimentacao") == -1).sum().alias("dismissals"),
            pl.col("saldo_movimentacao").sum().alias("balance"),
            salary_expr.median().alias("salary_median_admissions"),
        )
        .sort("admissions", descending=True)
    )
    _write_json(
        gold_dir / f"by-uf-{yearmonth}.json",
        {
            "competence": yearmonth,
            "source": "Novo CAGED / MTE",
            "items": by_uf.to_dicts(),
        },
    )

    by_occupation = (
        data.group_by(["cbo_familia", "cbo_codigo"])
        .agg(
            (pl.col("saldo_movimentacao") == 1).sum().alias("admissions"),
            (pl.col("saldo_movimentacao") == -1).sum().alias("dismissals"),
            pl.col("saldo_movimentacao").sum().alias("balance"),
            salary_expr.median().alias("salary_median_admissions"),
        )
        .sort("admissions", descending=True)
    )
    _write_json(
        gold_dir / f"by-occupation-{yearmonth}.json",
        {
            "competence": yearmonth,
            "source": "Novo CAGED / MTE",
            "items": by_occupation.to_dicts(),
        },
    )

    return parquet_path, overview_path
