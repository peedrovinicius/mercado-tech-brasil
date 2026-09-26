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

VALID_ADJUSTMENT_KINDS = {"FOR", "EXC"}


@dataclass(frozen=True)
class AdjustmentTransformResult:
    kind: str
    rows_read: int
    rows_valid: int
    rows_rejected: int
    rows_tech: int
    silver_path: Path
    reject_path: Path
    quality_path: Path


def add_adjustment_deltas(frame, *, kind: str):
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError("Polars não está instalado.") from exc

    normalized_kind = kind.upper().strip()
    if normalized_kind not in VALID_ADJUSTMENT_KINDS:
        raise ValueError(f"kind deve ser um de {sorted(VALID_ADJUSTMENT_KINDS)}")

    factor = -1 if normalized_kind == "EXC" else 1
    return frame.with_columns(
        pl.when(pl.col("saldo_movimentacao") == 1)
        .then(pl.lit(factor))
        .otherwise(pl.lit(0))
        .cast(pl.Int16)
        .alias("admissions_delta"),
        pl.when(pl.col("saldo_movimentacao") == -1)
        .then(pl.lit(factor))
        .otherwise(pl.lit(0))
        .cast(pl.Int16)
        .alias("dismissals_delta"),
        (pl.col("saldo_movimentacao") * factor)
        .cast(pl.Int16)
        .alias("balance_delta"),
        pl.lit(normalized_kind).alias("adjustment_kind"),
    )


def _load_tech_families(config_path: Path) -> set[str]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return {str(code) for code in payload["families"]}


def _effective_competence_expr(frame, kind: str, ingest_competence: str):
    import polars as pl

    candidates = (
        ["competencia_mov", "competencia_declarada"]
        if kind == "FOR"
        else ["competencia_mov", "competencia_declarada", "competencia_exclusao"]
    )
    existing = [name for name in candidates if name in frame.columns]

    if not existing:
        return pl.lit(ingest_competence).alias("effective_competence")

    expressions = [
        pl.col(name)
        .cast(pl.Utf8, strict=False)
        .str.replace_all(r"\D", "")
        .str.slice(0, 6)
        .replace("", None)
        for name in existing
    ]
    return pl.coalesce(expressions + [pl.lit(ingest_competence)]).alias(
        "effective_competence"
    )


def transform_adjustment_file(
    input_path: Path,
    *,
    ingest_competence: str,
    kind: str,
    silver_dir: Path,
    gold_dir: Path,
    cbo_config_path: Path,
) -> AdjustmentTransformResult:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError("Polars não está instalado.") from exc

    normalized_kind = kind.upper().strip()
    if normalized_kind not in VALID_ADJUSTMENT_KINDS:
        raise ValueError(f"kind deve ser um de {sorted(VALID_ADJUSTMENT_KINDS)}")
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
            "Layout de ajuste inesperado. Colunas obrigatórias ausentes: "
            + ", ".join(sorted(missing))
        )

    frame = frame.rename(normalized)
    renames = {
        col: COLUMN_RENAME[col]
        for col in frame.columns
        if col in COLUMN_RENAME
    }
    frame = frame.rename(renames)

    frame = frame.with_columns(
        pl.col("uf_codigo").cast(pl.Utf8, strict=False).str.strip_chars(),
        pl.col("cbo_codigo")
        .cast(pl.Utf8, strict=False)
        .str.replace_all(r"\D", "")
        .str.strip_chars(),
        pl.col("municipio_codigo_caged")
        .cast(pl.Utf8, strict=False)
        .str.replace_all(r"\D", "")
        .str.strip_chars(),
        pl.col("saldo_movimentacao")
        .cast(pl.Utf8, strict=False)
        .str.replace(",", ".")
        .cast(pl.Int16, strict=False),
        pl.when(
            pl.col("salario_mensal")
            .cast(pl.Utf8, strict=False)
            .str.contains(",", literal=True)
        )
        .then(
            pl.col("salario_mensal")
            .cast(pl.Utf8, strict=False)
            .str.replace_all(".", "", literal=True)
            .str.replace(",", ".")
        )
        .otherwise(pl.col("salario_mensal").cast(pl.Utf8, strict=False))
        .cast(pl.Float64, strict=False)
        .alias("salario_mensal"),
    ).with_columns(
        pl.col("uf_codigo").replace(UF_CODE_TO_SIGLA).alias("uf"),
        pl.col("cbo_codigo").str.slice(0, 4).alias("cbo_familia"),
        _effective_competence_expr(frame, normalized_kind, ingest_competence),
    )

    valid_ufs = list(UF_CODE_TO_SIGLA.values())
    frame = frame.with_columns(
        (~pl.col("uf").is_in(valid_ufs)).alias("erro_uf"),
        (
            pl.col("cbo_codigo").is_null()
            | (pl.col("cbo_codigo").str.len_chars() < 4)
        ).alias("erro_cbo"),
        (~pl.col("saldo_movimentacao").is_in([-1, 1])).alias("erro_saldo"),
        (
            pl.col("salario_mensal").is_not_null()
            & (pl.col("salario_mensal") < 0)
        ).alias("erro_salario"),
    ).with_columns(
        (
            pl.col("erro_uf")
            | pl.col("erro_cbo")
            | pl.col("erro_saldo")
            | pl.col("erro_salario")
        ).alias("registro_invalido")
    )

    valid = add_adjustment_deltas(
        frame.filter(~pl.col("registro_invalido")),
        kind=normalized_kind,
    )
    rejected = frame.filter(pl.col("registro_invalido"))
    tech_families = _load_tech_families(cbo_config_path)
    tech = valid.filter(pl.col("cbo_familia").is_in(list(tech_families)))

    silver_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    suffix = normalized_kind.lower()
    silver_path = silver_dir / f"caged_tech_{suffix}_{ingest_competence}.parquet"
    reject_path = silver_dir / f"caged_rejected_{suffix}_{ingest_competence}.parquet"
    quality_path = gold_dir / f"quality-{suffix}-{ingest_competence}.json"

    tech.write_parquet(silver_path, compression="zstd")
    rejected.write_parquet(reject_path, compression="zstd")

    report = {
        "source": "novo_caged",
        "file_kind": normalized_kind,
        "ingest_competence": ingest_competence,
        "rows_read": frame.height,
        "rows_valid": valid.height,
        "rows_rejected": rejected.height,
        "rows_tech": tech.height,
        "valid_rate": round(valid.height / frame.height, 8) if frame.height else 0,
        "effective_competencies": sorted(
            str(value)
            for value in tech["effective_competence"].drop_nulls().unique().to_list()
        ),
        "semantics": {
            "FOR": "acrescenta movimentações declaradas fora do prazo",
            "EXC": "inverte o efeito da movimentação original",
        }[normalized_kind],
    }
    quality_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return AdjustmentTransformResult(
        kind=normalized_kind,
        rows_read=frame.height,
        rows_valid=valid.height,
        rows_rejected=rejected.height,
        rows_tech=tech.height,
        silver_path=silver_path,
        reject_path=reject_path,
        quality_path=quality_path,
    )
