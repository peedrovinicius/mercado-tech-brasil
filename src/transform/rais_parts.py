from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from src.transform.rais_silver import REJECT_SCHEMA, SILVER_SCHEMA


SUM_FIELDS = (
    "rows_read",
    "rows_valid",
    "rows_rejected",
    "rows_active",
    "rows_inactive",
    "rows_active_source",
    "rows_inactive_source",
    "rows_unknown_status_source",
    "rows_year_mismatch_source",
    "rows_tech",
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def _find_parts(parts_root: Path, filename: str) -> list[Path]:
    return sorted(
        path
        for path in parts_root.rglob(filename)
        if path.is_file()
    )


def _merge_parquet(
    parts: list[Path],
    destination: Path,
    schema: pa.Schema,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)

    writer = pq.ParquetWriter(
        temporary,
        schema,
        compression="zstd",
    )
    try:
        for path in parts:
            parquet = pq.ParquetFile(path)
            if not parquet.schema_arrow.equals(schema):
                raise ValueError(
                    f"Schema Parquet RAIS divergente em {path}."
                )
            for batch in parquet.iter_batches(batch_size=100000):
                writer.write_table(
                    pa.Table.from_batches([batch], schema=schema)
                )
    except Exception:
        writer.close()
        temporary.unlink(missing_ok=True)
        raise
    else:
        writer.close()

    temporary.replace(destination)


def _merge_download_manifests(
    manifests: list[Path],
    *,
    year: int,
    destination: Path,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    seen_paths: set[str] = set()

    for path in manifests:
        payload = _read_json(path)
        if int(payload.get("year") or 0) != year:
            raise ValueError(
                f"Ano de manifesto RAIS divergente em {path}."
            )
        files = payload.get("files")
        if not isinstance(files, list) or len(files) != 1:
            raise ValueError(
                f"Manifesto regional RAIS inválido em {path}."
            )

        entry = files[0]
        if not isinstance(entry, dict):
            raise TypeError(
                f"Entrada de manifesto RAIS inválida em {path}."
            )

        source_path = str(entry.get("path") or "")
        sha256 = str(entry.get("sha256") or "")
        if not source_path or len(sha256) != 64:
            raise ValueError(
                f"Proveniência RAIS incompleta em {path}."
            )
        if source_path in seen_paths:
            raise ValueError(
                f"Arquivo RAIS duplicado no merge: {source_path}."
            )
        seen_paths.add(source_path)
        entries.append(entry)

    entries.sort(key=lambda item: str(item.get("path") or "").upper())
    transports = sorted(
        {
            str(item.get("transport") or "unknown")
            for item in entries
        }
    )
    payload: dict[str, object] = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": year,
        "dataset": "vinculos",
        "concept": "estoque anual de vínculos formais em 31/12",
        "transport": transports[0] if len(transports) == 1 else "mixed",
        "transports": transports,
        "files": entries,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def merge_rais_silver_parts(
    *,
    year: int,
    parts_root: Path,
    silver_dir: Path,
    bronze_archive_dir: Path,
) -> dict[str, Path]:
    quality_name = f"rais_quality_{year}.json"
    tech_name = f"rais_tech_{year}.parquet"
    reject_name = f"rais_rejected_{year}.parquet"

    quality_paths = _find_parts(parts_root, quality_name)
    tech_paths = _find_parts(parts_root, tech_name)
    reject_paths = _find_parts(parts_root, reject_name)
    manifest_paths = _find_parts(
        parts_root,
        "download-manifest-part.json",
    )

    part_count = len(quality_paths)
    if part_count < 1:
        raise FileNotFoundError(
            f"Nenhuma parte RAIS encontrada em {parts_root}."
        )
    if len(tech_paths) != part_count:
        raise ValueError(
            "Quantidade de Parquets tech difere da quantidade de relatórios."
        )
    if len(reject_paths) != part_count:
        raise ValueError(
            "Quantidade de Parquets de rejeição difere da quantidade de relatórios."
        )
    if len(manifest_paths) != part_count:
        raise ValueError(
            "Quantidade de manifests difere da quantidade de relatórios."
        )

    qualities = [_read_json(path) for path in quality_paths]
    if any(int(item.get("year") or 0) != year for item in qualities):
        raise ValueError("Partes RAIS possuem ano divergente.")

    totals = {
        field: sum(int(item.get(field) or 0) for item in qualities)
        for field in SUM_FIELDS
    }
    rejection_counts: Counter[str] = Counter()
    for item in qualities:
        raw_counts = item.get("rejection_counts") or {}
        if not isinstance(raw_counts, dict):
            raise TypeError("Contagem de rejeições RAIS inválida.")
        rejection_counts.update(
            {
                str(key): int(value or 0)
                for key, value in raw_counts.items()
            }
        )

    partition_total = (
        totals["rows_active_source"]
        + totals["rows_inactive_source"]
        + totals["rows_unknown_status_source"]
        + totals["rows_year_mismatch_source"]
    )
    partition_complete = (
        all(item.get("source_partition_complete") is True for item in qualities)
        and partition_total == totals["rows_read"]
    )

    silver_dir.mkdir(parents=True, exist_ok=True)
    tech_destination = silver_dir / tech_name
    reject_destination = silver_dir / reject_name
    quality_destination = silver_dir / quality_name

    _merge_parquet(tech_paths, tech_destination, SILVER_SCHEMA)
    _merge_parquet(reject_paths, reject_destination, REJECT_SCHEMA)

    manifest_destination = (
        bronze_archive_dir / "download-manifest.json"
    )
    manifest = _merge_download_manifests(
        manifest_paths,
        year=year,
        destination=manifest_destination,
    )

    quality: dict[str, object] = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": year,
        "scope": "vínculos ativos em 31/12 com recorte CBO tech v2",
        **totals,
        "source_partition_complete": partition_complete,
        "valid_rate": (
            round(totals["rows_valid"] / totals["rows_read"], 8)
            if totals["rows_read"]
            else 0
        ),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "parts_merged": part_count,
        "source_archives": [
            str(item.get("path") or "")
            for item in manifest["files"]
            if isinstance(item, dict)
        ],
        "year_source": "annual_context",
        "uf_source": "municipality_code_prefix",
        "cbo_normalization": (
            "5 digit numeric codes are left padded to 6 digits"
        ),
        "silver_path": tech_destination.name,
        "reject_path": reject_destination.name,
        "gold_ready": False,
        "publication_ready": False,
        "note": (
            "Qualidade nacional obtida pela soma das partes regionais "
            "processadas independentemente. A publicação permanece bloqueada."
        ),
    }
    quality_destination.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "silver": tech_destination,
        "rejects": reject_destination,
        "quality": quality_destination,
        "manifest": manifest_destination,
    }
