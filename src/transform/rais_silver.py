from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from src.transform.rais_value_semantics import normalize_value


@dataclass(frozen=True)
class RaisSilverResult:
    rows_read: int
    rows_active: int
    rows_inactive: int
    rows_active_source: int
    rows_inactive_source: int
    rows_unknown_status_source: int
    rows_year_mismatch_source: int
    rows_valid: int
    rows_rejected: int
    rows_tech: int
    silver_path: Path
    reject_path: Path
    quality_path: Path


SILVER_SCHEMA = pa.schema(
    [
        ("year", pa.int16()),
        ("cbo_codigo", pa.string()),
        ("cbo_familia", pa.string()),
        ("municipio_codigo", pa.string()),
        ("uf", pa.string()),
        ("active_3112", pa.bool_()),
        ("source_file", pa.string()),
    ]
)

REJECT_SCHEMA = pa.schema(
    [
        ("source_file", pa.string()),
        ("year_raw", pa.string()),
        ("cbo_raw", pa.string()),
        ("municipio_raw", pa.string()),
        ("uf_raw", pa.string()),
        ("active_raw", pa.string()),
        ("reason", pa.string()),
    ]
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def _load_tech_families(path: Path) -> set[str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, dict) or not families:
        raise ValueError("Configuração CBO tech inválida.")
    return {str(code) for code in families}


def _single_file(root: Path, filename: str) -> Path:
    matches = [path for path in root.rglob(filename) if path.is_file()]
    if len(matches) != 1:
        raise ValueError(
            f"Esperado exatamente um arquivo {filename} em {root}; "
            f"encontrados: {len(matches)}"
        )
    return matches[0]


def _column_mapping(
    semantic_item: dict[str, Any],
    layout_item: dict[str, Any],
) -> dict[str, str]:
    original = layout_item.get("columns") or []
    normalized = layout_item.get("normalized_columns") or []
    normalized_to_original = {
        str(normalized_name): str(original_name)
        for original_name, normalized_name in zip(
            original,
            normalized,
            strict=True,
        )
    }

    result: dict[str, str] = {}
    required = semantic_item.get("required") or {}
    for concept in ("year", "cbo_occupation", "municipality", "uf", "active_3112"):
        item = required.get(concept) or {}
        matches = item.get("matches") or []
        if item.get("status") != "matched" or len(matches) != 1:
            raise ValueError(
                f"Conceito {concept} não está resolvido em "
                f"{semantic_item.get('file')}."
            )
        normalized_name = str(matches[0])
        original_name = normalized_to_original.get(normalized_name)
        if original_name is None:
            raise ValueError(
                f"Coluna {normalized_name} não existe no layout de "
                f"{semantic_item.get('file')}."
            )
        result[concept] = original_name
    return result


def _digits(value: object) -> str:
    return re.sub(r"\D", "", str(value or "").strip())


def _flush(
    writer: pq.ParquetWriter,
    rows: list[dict[str, object]],
    schema: pa.Schema,
) -> None:
    if not rows:
        return
    writer.write_table(pa.Table.from_pylist(rows, schema=schema))
    rows.clear()


def transform_rais_year(
    *,
    year: int,
    extracted_dir: Path,
    layout_report_path: Path,
    semantic_report_path: Path,
    value_semantics_report_path: Path,
    cbo_config_path: Path,
    silver_dir: Path,
    batch_size: int = 50000,
) -> RaisSilverResult:
    if batch_size < 1000 or batch_size > 500000:
        raise ValueError("batch_size deve estar entre 1000 e 500000.")

    layout = _load_json(layout_report_path)
    semantics = _load_json(semantic_report_path)
    value_semantics = _load_json(value_semantics_report_path)

    if semantics.get("silver_ready") is not True:
        raise ValueError("Layout RAIS ainda não está pronto para Silver.")
    if value_semantics.get("silver_transform_ready") is not True:
        raise ValueError("Semântica de valores RAIS ainda não está pronta para Silver.")
    if int(semantics.get("year") or 0) != year:
        raise ValueError("Ano do relatório semântico difere do ano solicitado.")
    if int(value_semantics.get("year") or 0) != year:
        raise ValueError("Ano do relatório de valores difere do ano solicitado.")

    active_values = {
        normalize_value(value)
        for value in (
            value_semantics.get("active_3112", {}).get("official_active_values") or []
        )
    }
    inactive_values = {
        normalize_value(value)
        for value in (
            value_semantics.get("active_3112", {}).get("official_inactive_values") or []
        )
    }
    if not active_values or not inactive_values:
        raise ValueError("Relatório de valores não define categorias ativas e inativas.")

    tech_families = _load_tech_families(cbo_config_path)
    layout_files = {
        str(item.get("file")): item
        for item in layout.get("files", [])
        if isinstance(item, dict)
    }
    semantic_files = [
        item
        for item in semantics.get("files", [])
        if isinstance(item, dict)
    ]
    if not semantic_files:
        raise ValueError("Relatório semântico não possui arquivos.")

    silver_dir.mkdir(parents=True, exist_ok=True)
    silver_path = silver_dir / f"rais_tech_{year}.parquet"
    reject_path = silver_dir / f"rais_rejected_{year}.parquet"
    quality_path = silver_dir / f"rais_quality_{year}.json"

    silver_tmp = silver_path.with_suffix(".parquet.tmp")
    reject_tmp = reject_path.with_suffix(".parquet.tmp")
    silver_tmp.unlink(missing_ok=True)
    reject_tmp.unlink(missing_ok=True)

    silver_writer = pq.ParquetWriter(
        silver_tmp,
        SILVER_SCHEMA,
        compression="zstd",
    )
    reject_writer = pq.ParquetWriter(
        reject_tmp,
        REJECT_SCHEMA,
        compression="zstd",
    )

    tech_buffer: list[dict[str, object]] = []
    reject_buffer: list[dict[str, object]] = []

    rows_read = 0
    rows_active = 0
    rows_inactive = 0
    rows_active_source = 0
    rows_inactive_source = 0
    rows_unknown_status_source = 0
    rows_year_mismatch_source = 0
    rows_valid = 0
    rows_rejected = 0
    rows_tech = 0
    rejection_counts: dict[str, int] = {
        "invalid_year": 0,
        "invalid_active_status": 0,
        "invalid_cbo": 0,
        "missing_municipality": 0,
        "invalid_uf": 0,
    }

    try:
        for semantic_item in semantic_files:
            filename = str(semantic_item.get("file") or "")
            layout_item = layout_files.get(filename)
            if not filename or not isinstance(layout_item, dict):
                raise ValueError(f"Layout estrutural ausente para {filename!r}.")

            columns = _column_mapping(semantic_item, layout_item)
            source = _single_file(extracted_dir, filename)
            encoding = str(layout_item.get("encoding") or "")
            delimiter = str(layout_item.get("delimiter") or "")
            if not encoding or not delimiter:
                raise ValueError(f"Encoding ou delimitador ausente para {filename}.")

            with source.open(
                "r",
                encoding=encoding,
                errors="strict",
                newline="",
            ) as handle:
                reader = csv.DictReader(handle, delimiter=delimiter)
                if reader.fieldnames is None:
                    raise ValueError(f"Cabeçalho ausente em {filename}.")

                for row in reader:
                    rows_read += 1

                    year_raw = str(row.get(columns["year"]) or "").strip()
                    cbo_raw = str(row.get(columns["cbo_occupation"]) or "").strip()
                    municipality_raw = str(
                        row.get(columns["municipality"]) or ""
                    ).strip()
                    uf_raw = str(row.get(columns["uf"]) or "").strip()
                    active_raw = str(row.get(columns["active_3112"]) or "").strip()

                    active_normalized = normalize_value(active_raw)
                    cbo_code = _digits(cbo_raw)
                    municipality_code = _digits(municipality_raw)
                    uf = uf_raw.strip().upper()

                    if year_raw != str(year):
                        rows_year_mismatch_source += 1
                    elif active_normalized in active_values:
                        rows_active_source += 1
                    elif active_normalized in inactive_values:
                        rows_inactive_source += 1
                    else:
                        rows_unknown_status_source += 1

                    reasons: list[str] = []
                    if year_raw != str(year):
                        reasons.append("invalid_year")
                    if active_normalized not in active_values | inactive_values:
                        reasons.append("invalid_active_status")
                    if len(cbo_code) < 4:
                        reasons.append("invalid_cbo")
                    if not municipality_code:
                        reasons.append("missing_municipality")
                    if len(uf) != 2 or not uf.isalpha():
                        reasons.append("invalid_uf")

                    if reasons:
                        rows_rejected += 1
                        for reason in reasons:
                            rejection_counts[reason] += 1
                        reject_buffer.append(
                            {
                                "source_file": filename,
                                "year_raw": year_raw,
                                "cbo_raw": cbo_raw,
                                "municipio_raw": municipality_raw,
                                "uf_raw": uf_raw,
                                "active_raw": active_raw,
                                "reason": ",".join(reasons),
                            }
                        )
                        if len(reject_buffer) >= batch_size:
                            _flush(reject_writer, reject_buffer, REJECT_SCHEMA)
                        continue

                    rows_valid += 1
                    if active_normalized in inactive_values:
                        rows_inactive += 1
                        continue

                    rows_active += 1
                    family = cbo_code[:4]
                    if family not in tech_families:
                        continue

                    rows_tech += 1
                    tech_buffer.append(
                        {
                            "year": year,
                            "cbo_codigo": cbo_code,
                            "cbo_familia": family,
                            "municipio_codigo": municipality_code,
                            "uf": uf,
                            "active_3112": True,
                            "source_file": filename,
                        }
                    )
                    if len(tech_buffer) >= batch_size:
                        _flush(silver_writer, tech_buffer, SILVER_SCHEMA)

        _flush(silver_writer, tech_buffer, SILVER_SCHEMA)
        _flush(reject_writer, reject_buffer, REJECT_SCHEMA)
    except Exception:
        silver_writer.close()
        reject_writer.close()
        silver_tmp.unlink(missing_ok=True)
        reject_tmp.unlink(missing_ok=True)
        raise
    else:
        silver_writer.close()
        reject_writer.close()

    silver_tmp.replace(silver_path)
    reject_tmp.replace(reject_path)

    quality = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": year,
        "scope": "vínculos ativos em 31/12 com recorte CBO tech v2",
        "rows_read": rows_read,
        "rows_valid": rows_valid,
        "rows_rejected": rows_rejected,
        "rows_active": rows_active,
        "rows_inactive": rows_inactive,
        "rows_active_source": rows_active_source,
        "rows_inactive_source": rows_inactive_source,
        "rows_unknown_status_source": rows_unknown_status_source,
        "rows_year_mismatch_source": rows_year_mismatch_source,
        "source_partition_complete": (
            rows_read
            == rows_active_source
            + rows_inactive_source
            + rows_unknown_status_source
            + rows_year_mismatch_source
        ),
        "rows_tech": rows_tech,
        "valid_rate": round(rows_valid / rows_read, 8) if rows_read else 0,
        "rejection_counts": rejection_counts,
        "cbo_families": sorted(tech_families),
        "silver_path": silver_path.name,
        "reject_path": reject_path.name,
        "gold_ready": False,
        "publication_ready": False,
        "note": (
            "A transformação Silver não autoriza publicação. O estoque anual "
            "ainda precisa de reconciliação oficial, Gold e gate específico."
        ),
    }
    quality_path.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return RaisSilverResult(
        rows_read=rows_read,
        rows_active=rows_active,
        rows_inactive=rows_inactive,
        rows_active_source=rows_active_source,
        rows_inactive_source=rows_inactive_source,
        rows_unknown_status_source=rows_unknown_status_source,
        rows_year_mismatch_source=rows_year_mismatch_source,
        rows_valid=rows_valid,
        rows_rejected=rows_rejected,
        rows_tech=rows_tech,
        silver_path=silver_path,
        reject_path=reject_path,
        quality_path=quality_path,
    )
