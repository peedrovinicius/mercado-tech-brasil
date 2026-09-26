import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.transform.rais_parts import merge_rais_silver_parts
from src.transform.rais_silver import REJECT_SCHEMA, SILVER_SCHEMA


def _write_part(
    root: Path,
    *,
    key: str,
    year: int,
    source_file: str,
    active: int,
    inactive: int,
    tech_rows: list[dict[str, object]],
    reject_rows: list[dict[str, object]],
) -> None:
    part = root / key
    part.mkdir(parents=True)

    pq.write_table(
        pa.Table.from_pylist(tech_rows, schema=SILVER_SCHEMA),
        part / f"rais_tech_{year}.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(reject_rows, schema=REJECT_SCHEMA),
        part / f"rais_rejected_{year}.parquet",
    )

    rows_read = active + inactive
    quality = {
        "year": year,
        "rows_read": rows_read,
        "rows_valid": rows_read - len(reject_rows),
        "rows_rejected": len(reject_rows),
        "rows_active": len(tech_rows),
        "rows_inactive": inactive,
        "rows_active_source": active,
        "rows_inactive_source": inactive,
        "rows_unknown_status_source": 0,
        "rows_year_mismatch_source": 0,
        "rows_tech": len(tech_rows),
        "source_partition_complete": True,
        "rejection_counts": {
            "invalid_active_status": 0,
            "invalid_cbo": len(reject_rows),
            "invalid_municipality": 0,
            "invalid_uf": 0,
        },
    }
    (part / f"rais_quality_{year}.json").write_text(
        json.dumps(quality),
        encoding="utf-8",
    )

    manifest = {
        "year": year,
        "files": [
            {
                "path": source_file,
                "sha256": (key[0] * 64),
                "size_bytes": 100,
                "source_url": f"ftp://example/{source_file}",
            }
        ],
    }
    (part / "download-manifest-part.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def test_merge_rais_parts_builds_national_quality_and_parquet(
    tmp_path: Path,
):
    parts = tmp_path / "parts"
    silver = tmp_path / "silver"
    bronze = tmp_path / "bronze"

    _write_part(
        parts,
        key="a",
        year=2025,
        source_file="RAIS_VINC_A.7z",
        active=3,
        inactive=1,
        tech_rows=[
            {
                "year": 2025,
                "cbo_codigo": "212405",
                "cbo_familia": "2124",
                "municipio_codigo": "230440",
                "uf": "CE",
                "active_3112": True,
                "source_file": "A.COMT",
            }
        ],
        reject_rows=[],
    )
    _write_part(
        parts,
        key="b",
        year=2025,
        source_file="RAIS_VINC_B.7z",
        active=2,
        inactive=2,
        tech_rows=[
            {
                "year": 2025,
                "cbo_codigo": "317110",
                "cbo_familia": "3171",
                "municipio_codigo": "355030",
                "uf": "SP",
                "active_3112": True,
                "source_file": "B.COMT",
            }
        ],
        reject_rows=[
            {
                "source_file": "B.COMT",
                "year_context": "2025",
                "cbo_raw": "",
                "municipio_raw": "355030",
                "uf_derived": "SP",
                "active_raw": "1",
                "reason": "invalid_cbo",
            }
        ],
    )

    paths = merge_rais_silver_parts(
        year=2025,
        parts_root=parts,
        silver_dir=silver,
        bronze_archive_dir=bronze,
    )

    quality = json.loads(
        paths["quality"].read_text(encoding="utf-8")
    )
    assert quality["parts_merged"] == 2
    assert quality["rows_read"] == 8
    assert quality["rows_active_source"] == 5
    assert quality["rows_inactive_source"] == 3
    assert quality["rows_tech"] == 2
    assert quality["rows_rejected"] == 1
    assert quality["source_partition_complete"] is True
    assert quality["source_archives"] == [
        "RAIS_VINC_A.7z",
        "RAIS_VINC_B.7z",
    ]

    tech = pq.read_table(paths["silver"])
    rejects = pq.read_table(paths["rejects"])
    assert tech.num_rows == 2
    assert rejects.num_rows == 1

    manifest = json.loads(
        paths["manifest"].read_text(encoding="utf-8")
    )
    assert len(manifest["files"]) == 2
