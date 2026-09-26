from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.methodology.salary import add_salary_eligibility, methodology_for_competence


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _ensure_delta_columns(frame, *, yearmonth: str):
    import polars as pl

    expressions = []
    if "admissions_delta" not in frame.columns:
        expressions.append(
            (pl.col("saldo_movimentacao") == 1)
            .cast(pl.Int16)
            .alias("admissions_delta")
        )
    if "dismissals_delta" not in frame.columns:
        expressions.append(
            (pl.col("saldo_movimentacao") == -1)
            .cast(pl.Int16)
            .alias("dismissals_delta")
        )
    if "balance_delta" not in frame.columns:
        expressions.append(
            pl.col("saldo_movimentacao").cast(pl.Int16).alias("balance_delta")
        )
    if "effective_competence" not in frame.columns:
        expressions.append(pl.lit(yearmonth).alias("effective_competence"))
    if "adjustment_kind" not in frame.columns:
        expressions.append(pl.lit("MOV").alias("adjustment_kind"))

    return frame.with_columns(*expressions) if expressions else frame


def _load_contributing_data(silver_path: Path, *, yearmonth: str):
    import polars as pl

    base = _ensure_delta_columns(
        pl.read_parquet(silver_path),
        yearmonth=yearmonth,
    )

    frames = [base]
    for pattern in ("caged_tech_for_*.parquet", "caged_tech_exc_*.parquet"):
        for path in sorted(silver_path.parent.glob(pattern)):
            adjustment = pl.read_parquet(path)
            if "effective_competence" not in adjustment.columns:
                continue
            adjustment = adjustment.filter(
                pl.col("effective_competence").cast(pl.Utf8) == yearmonth
            )
            if adjustment.height:
                frames.append(adjustment)

    if len(frames) == 1:
        return base

    return pl.concat(frames, how="diagonal_relaxed")


def _weighted_median(values: list[tuple[float, int]]) -> float | None:
    positive = sorted(
        (float(value), int(weight))
        for value, weight in values
        if int(weight) > 0
    )
    total = sum(weight for _, weight in positive)
    if total <= 0:
        return None

    def value_at(position: int) -> float:
        cumulative = 0
        for value, weight in positive:
            cumulative += weight
            if cumulative >= position:
                return value
        raise RuntimeError("Posição de mediana fora da distribuição.")

    if total % 2:
        return value_at(total // 2 + 1)

    left = value_at(total // 2)
    right = value_at(total // 2 + 1)
    return (left + right) / 2


def _salary_stats(frame, *, group_cols: list[str]) -> dict[tuple[Any, ...], dict[str, float | int | None]]:
    import polars as pl

    eligible = frame.filter(
        pl.col("salario_admissao_elegivel")
        & (pl.col("admissions_delta") != 0)
    )

    if not eligible.height:
        return {}

    frequency = (
        eligible.group_by(group_cols + ["salario_mensal"])
        .agg(pl.col("admissions_delta").sum().alias("weight"))
        .filter(pl.col("weight") > 0)
    )

    buckets: dict[tuple[Any, ...], list[tuple[float, int]]] = defaultdict(list)
    for row in frequency.to_dicts():
        key = tuple(row[column] for column in group_cols)
        buckets[key].append((float(row["salario_mensal"]), int(row["weight"])))

    result: dict[tuple[Any, ...], dict[str, float | int | None]] = {}
    for key, values in buckets.items():
        count = sum(weight for _, weight in values)
        weighted_sum = sum(value * weight for value, weight in values)
        result[key] = {
            "count": count,
            "mean": weighted_sum / count if count else None,
            "median": _weighted_median(values),
        }
    return result


def _validate_nonnegative_counts(frame, *, label: str) -> None:
    import polars as pl

    invalid = frame.filter(
        (pl.col("admissions") < 0) | (pl.col("dismissals") < 0)
    )
    if invalid.height:
        raise ValueError(
            f"{label}: ajustes produziram contagem negativa. "
            "Verifique se todas as competências base necessárias foram ingeridas."
        )


def _build_grouped(
    data,
    *,
    group_cols: list[str],
    salary_stats: dict[tuple[Any, ...], dict[str, float | int | None]],
):
    import polars as pl

    grouped = (
        data.group_by(group_cols)
        .agg(
            pl.col("admissions_delta").sum().alias("admissions"),
            pl.col("dismissals_delta").sum().alias("dismissals"),
            pl.col("balance_delta").sum().alias("balance"),
        )
        .sort("admissions", descending=True)
    )
    _validate_nonnegative_counts(grouped, label="Gold")

    items = []
    for row in grouped.to_dicts():
        key = tuple(row[column] for column in group_cols)
        stats = salary_stats.get(key, {})
        items.append(
            {
                **row,
                "salary_mean_admissions": stats.get("mean"),
                "salary_median_admissions": stats.get("median"),
                "salary_eligible_admissions": stats.get("count", 0),
            }
        )
    return items


def _rebuild_trend(gold_dir: Path) -> Path:
    items: list[dict[str, object]] = []
    for path in sorted(gold_dir.glob("overview-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        competence = str(payload.get("competence") or "")
        if len(competence) != 6:
            continue
        items.append(
            {
                "competence": competence,
                "admissions": payload.get("admissions"),
                "dismissals": payload.get("dismissals"),
                "balance": payload.get("balance"),
                "salary_mean_admissions": payload.get("salary_mean_admissions"),
                "salary_median_admissions": payload.get("salary_median_admissions"),
            }
        )

    destination = gold_dir / "trend.json"
    _write_json(
        destination,
        {
            "source": "Novo CAGED / MTE",
            "scope": "recorte CBO de tecnologia versionado",
            "items": sorted(items, key=lambda item: str(item["competence"])),
        },
    )
    return destination


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

    data = _load_contributing_data(silver_path, yearmonth=yearmonth)
    data = add_salary_eligibility(data, yearmonth=yearmonth)
    salary_methodology = methodology_for_competence(yearmonth)

    counts = data.select(
        pl.col("admissions_delta").sum().alias("admissions"),
        pl.col("dismissals_delta").sum().alias("dismissals"),
        pl.col("balance_delta").sum().alias("balance"),
    ).to_dicts()[0]

    admissions = int(counts["admissions"] or 0)
    dismissals = int(counts["dismissals"] or 0)
    balance = int(counts["balance"] or 0)

    if admissions < 0 or dismissals < 0:
        raise ValueError(
            "Ajustes produziram totais negativos. "
            "A série necessária para a reconstrução está incompleta."
        )
    if admissions - dismissals != balance:
        raise ValueError("Gold inconsistente: admissões menos desligamentos difere do saldo.")

    overall_salary = _salary_stats(data, group_cols=[])
    salary = overall_salary.get((), {})

    gold_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = gold_dir / f"market-{yearmonth}.parquet"
    overview_path = gold_dir / f"overview-{yearmonth}.json"

    summary = (
        data.group_by(["uf", "cbo_familia", "cbo_codigo"])
        .agg(
            pl.col("admissions_delta").sum().alias("admissoes"),
            pl.col("dismissals_delta").sum().alias("desligamentos"),
            pl.col("balance_delta").sum().alias("saldo"),
        )
        .with_columns(pl.lit(yearmonth).alias("competencia"))
        .sort(["uf", "cbo_familia", "cbo_codigo"])
    )
    summary.write_parquet(parquet_path, compression="zstd")

    adjustment_counts = (
        data.group_by("adjustment_kind")
        .len()
        .sort("adjustment_kind")
        .to_dicts()
    )

    overview = {
        "competence": yearmonth,
        "scope": "recorte CBO de tecnologia versionado",
        "admissions": admissions,
        "dismissals": dismissals,
        "balance": balance,
        "salary_mean_admissions": salary.get("mean"),
        "salary_median_admissions": salary.get("median"),
        "salary_eligible_admissions": salary.get("count", 0),
        "salary_methodology": {
            "minimum_wage_brl": salary_methodology.minimum_wage_brl,
            "minimum_salary_brl": salary_methodology.minimum_salary_brl,
            "maximum_salary_brl": salary_methodology.maximum_salary_brl,
            "exclude_intermittent": True,
            "source": "MTE: Sumário Executivo Novo Caged",
        },
        "records_tech": data.height,
        "adjustments": adjustment_counts,
        "source": "Novo CAGED / MTE",
        "status": "generated_from_official_microdata",
    }
    _write_json(overview_path, overview)

    uf_salary = _salary_stats(data, group_cols=["uf"])
    _write_json(
        gold_dir / f"by-uf-{yearmonth}.json",
        {
            "competence": yearmonth,
            "source": "Novo CAGED / MTE",
            "items": _build_grouped(
                data,
                group_cols=["uf"],
                salary_stats=uf_salary,
            ),
        },
    )

    occupation_salary = _salary_stats(
        data,
        group_cols=["cbo_familia", "cbo_codigo"],
    )
    _write_json(
        gold_dir / f"by-occupation-{yearmonth}.json",
        {
            "competence": yearmonth,
            "source": "Novo CAGED / MTE",
            "items": _build_grouped(
                data,
                group_cols=["cbo_familia", "cbo_codigo"],
                salary_stats=occupation_salary,
            ),
        },
    )

    if "municipio_codigo_caged" in data.columns:
        municipality_salary = _salary_stats(
            data,
            group_cols=["municipio_codigo_caged"],
        )
        _write_json(
            gold_dir / f"by-municipality-{yearmonth}.json",
            {
                "competence": yearmonth,
                "source": "Novo CAGED / MTE",
                "code_system": "codigo_municipio_caged",
                "items": _build_grouped(
                    data,
                    group_cols=["municipio_codigo_caged"],
                    salary_stats=municipality_salary,
                ),
            },
        )

    _rebuild_trend(gold_dir)
    return parquet_path, overview_path
