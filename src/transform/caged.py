from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.transform.schema import (
    COLUMN_RENAME,
    UF_CODE_TO_SIGLA,
    normalize_column_name,
    validate_core_columns,
)


@dataclass(frozen=True)
class TransformResult:
    rows_read: int
    rows_valid: int
    rows_rejected: int
    rows_tech: int
    silver_path: Path
    reject_path: Path
    quality_path: Path


def _load_tech_families(config_path: Path) -> set[str]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {str(code) for code in payload["families"]}


def transform_mov_file(
    input_path: Path,
    *,
    yearmonth: str,
    silver_dir: Path,
    gold_dir: Path,
    cbo_config_path: Path,
) -> TransformResult:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError(
            "Polars não está instalado. Execute `pip install -e .`."
        ) from exc

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    frame = pl.read_csv(
        input_path,
        separator=";",
        encoding="utf8-lossy",
        infer_schema=False,
        null_values=["", "NA", "N/A"],
        truncate_ragged_lines=False,
    )

    original_columns = list(frame.columns)
    normalized = {col: normalize_column_name(col) for col in original_columns}
    missing = validate_core_columns(set(normalized.values()))
    if missing:
        raise ValueError(
            "Layout oficial inesperado. Colunas obrigatórias ausentes: "
            + ", ".join(sorted(missing))
        )

    frame = frame.rename(normalized)
    renames = {
        col: COLUMN_RENAME[col]
        for col in frame.columns
        if col in COLUMN_RENAME
    }
    frame = frame.rename(renames)

    tech_families = _load_tech_families(cbo_config_path)

    frame = frame.with_columns(
        pl.col("uf_codigo").str.strip_chars(),
        pl.col("cbo_codigo").str.replace_all(r"\D", "").str.strip_chars(),
        pl.col("municipio_codigo_caged").str.replace_all(r"\D", "").str.strip_chars(),
        pl.col("saldo_movimentacao").str.replace(",", ".").cast(pl.Int16, strict=False),
        pl.col("tipo_movimentacao").str.replace_all(r"\D", "").cast(pl.Int16, strict=False),
        pl.when(pl.col("salario_mensal").str.contains(",", literal=True))
        .then(
            pl.col("salario_mensal")
            .str.replace_all(".", "", literal=True)
            .str.replace(",", ".")
        )
        .otherwise(pl.col("salario_mensal"))
        .cast(pl.Float64, strict=False)
        .alias("salario_mensal"),
    ).with_columns(
        pl.col("uf_codigo").replace(UF_CODE_TO_SIGLA).alias("uf"),
        pl.col("cbo_codigo").str.slice(0, 4).alias("cbo_familia"),
        pl.when(pl.col("saldo_movimentacao") == 1)
        .then(pl.lit("admissao"))
        .when(pl.col("saldo_movimentacao") == -1)
        .then(pl.lit("desligamento"))
        .otherwise(pl.lit(None))
        .alias("movimento"),
    )

    valid_ufs = list(UF_CODE_TO_SIGLA.values())
    frame = frame.with_columns(
        (~pl.col("uf").is_in(valid_ufs)).alias("erro_uf"),
        (pl.col("cbo_codigo").is_null() | (pl.col("cbo_codigo").str.len_chars() < 4)).alias("erro_cbo"),
        (~pl.col("saldo_movimentacao").is_in([-1, 1])).alias("erro_saldo"),
        (pl.col("salario_mensal").is_not_null() & (pl.col("salario_mensal") < 0)).alias("erro_salario"),
    ).with_columns(
        (pl.col("erro_uf") | pl.col("erro_cbo") | pl.col("erro_saldo") | pl.col("erro_salario")).alias("registro_invalido")
    )

    valid = frame.filter(~pl.col("registro_invalido"))
    rejected = frame.filter(pl.col("registro_invalido"))
    tech = valid.filter(pl.col("cbo_familia").is_in(list(tech_families)))

    silver_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    silver_path = silver_dir / f"caged_tech_{yearmonth}.parquet"
    reject_path = silver_dir / f"caged_rejected_{yearmonth}.parquet"
    quality_path = gold_dir / f"quality-{yearmonth}.json"

    tech.write_parquet(silver_path, compression="zstd")
    rejected.write_parquet(reject_path, compression="zstd")

    rows_read = frame.height
    rows_valid = valid.height
    rows_rejected = rejected.height
    rows_tech = tech.height

    rejection_counts = {
        "invalid_uf": rejected.filter(pl.col("erro_uf")).height,
        "invalid_cbo": rejected.filter(pl.col("erro_cbo")).height,
        "invalid_saldo": rejected.filter(pl.col("erro_saldo")).height,
        "invalid_salary": rejected.filter(pl.col("erro_salario")).height,
    }

    report = {
        "source": "novo_caged",
        "file_kind": "MOV",
        "competence": yearmonth,
        "rows_read": rows_read,
        "rows_valid": rows_valid,
        "rows_rejected": rows_rejected,
        "rows_tech": rows_tech,
        "valid_rate": round(rows_valid / rows_read, 8) if rows_read else 0,
        "rejection_counts": rejection_counts,
        "layout_columns": original_columns,
        "publication_ready": False,
        "publication_gate": "awaiting_first_official_run_and_methodology_review",
        "note": (
            "Nenhum mês é marcado automaticamente como pronto para publicação na primeira "
            "execução. Após validar layout, rejeições e metodologia, o gate poderá ser promovido."
        ),
    }
    quality_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return TransformResult(
        rows_read=rows_read,
        rows_valid=rows_valid,
        rows_rejected=rows_rejected,
        rows_tech=rows_tech,
        silver_path=silver_path,
        reject_path=reject_path,
        quality_path=quality_path,
    )
