from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src.core.settings import settings
from src.ingestion.rais import (
    RaisRemoteFile,
    download_file,
    extract_year,
    write_download_manifest,
)
from src.transform.rais_profile import profile_rais_values
from src.transform.rais_schema import inspect_rais_directory
from src.transform.rais_semantics import validate_layout_semantics
from src.transform.rais_silver import transform_rais_year
from src.transform.rais_value_semantics import validate_value_semantics


def process_part(
    *,
    year: int,
    filename: str,
    key: str,
    remote_size: int,
    work_root: Path,
    local_archive: Path | None = None,
    transport: str = "ftp_mte",
    transport_url: str | None = None,
) -> Path:
    if year != 2025:
        raise ValueError("Este executor integral está travado na RAIS 2025.")
    if remote_size <= 0:
        raise ValueError("Tamanho remoto inválido.")

    work = work_root / key
    archives = work / "archives"
    extracted = work / "extracted"
    reports = work / "reports"
    silver = work / "silver"
    reports.mkdir(parents=True, exist_ok=True)

    remote = RaisRemoteFile(
        year=year,
        dataset="vinculos",
        filename=filename,
    )
    if local_archive is not None:
        if not local_archive.exists():
            raise FileNotFoundError(local_archive)
        archives.mkdir(parents=True, exist_ok=True)
        archive = archives / filename
        if archive.exists():
            archive.unlink()
        shutil.move(str(local_archive), archive)
    else:
        archive = download_file(
            remote,
            archives,
            max_attempts=5,
        )

    if archive.stat().st_size != remote_size:
        raise RuntimeError(
            "Tamanho local diverge do remoto: "
            f"{archive.stat().st_size}/{remote_size}"
        )

    part_manifest = work / "download-manifest-part.json"
    write_download_manifest(
        year,
        [archive],
        part_manifest,
        dataset="vinculos",
        transport=transport,
        transport_url=transport_url,
    )

    extracted_files = extract_year(
        year,
        archives,
        extracted,
    )
    if len(extracted_files) != 1:
        raise RuntimeError(
            f"Esperado 1 arquivo extraído em {filename}; "
            f"obtidos {len(extracted_files)}."
        )

    layout_path = reports / "layout-report.json"
    semantic_path = reports / "semantic-layout-report.json"
    profile_path = reports / "value-profile.json"
    values_path = reports / "value-semantics-report.json"

    layout = inspect_rais_directory(
        extracted,
        year=year,
        destination=layout_path,
    )
    semantic = validate_layout_semantics(
        layout_path,
        settings.root / "config" / "rais_semantic_contract.yml",
        semantic_path,
    )
    if semantic.get("silver_ready") is not True:
        raise RuntimeError(
            f"Layout regional não aprovado: {filename}"
        )

    profile_rais_values(
        extracted,
        layout_path,
        semantic_path,
        profile_path,
        max_rows_per_file=10000,
    )
    values = validate_value_semantics(
        profile_path,
        settings.root / "config" / "rais_value_semantics.yml",
        values_path,
        year=year,
    )
    if values.get("silver_transform_ready") is not True:
        raise RuntimeError(
            f"Valores regionais não aprovados: {filename}"
        )

    result = transform_rais_year(
        year=year,
        extracted_dir=extracted,
        layout_report_path=layout_path,
        semantic_report_path=semantic_path,
        value_semantics_report_path=values_path,
        cbo_config_path=settings.cbo_config_path,
        silver_dir=silver,
        batch_size=100000,
    )

    manifest_payload = json.loads(
        part_manifest.read_text(encoding="utf-8")
    )
    entry = manifest_payload["files"][0]
    summary = {
        "year": year,
        "key": key,
        "archive": filename,
        "remote_size": remote_size,
        "sha256": entry["sha256"],
        "transport": transport,
        "transport_url": transport_url or entry.get("source_url"),
        "official_source_url": entry.get("source_url"),
        "layout_signatures": layout["layout_signatures"],
        "semantic_valid": semantic["semantic_valid"],
        "value_semantics_valid": values["value_semantics_valid"],
        "rows_read": result.rows_read,
        "rows_active_source": result.rows_active_source,
        "rows_inactive_source": result.rows_inactive_source,
        "rows_unknown_status_source": result.rows_unknown_status_source,
        "rows_rejected": result.rows_rejected,
        "rows_tech": result.rows_tech,
    }
    summary_path = work / "part-summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for extracted_file in extracted_files:
        manifest_path = extracted_file.with_suffix(
            extracted_file.suffix + ".manifest.json"
        )
        if manifest_path.exists():
            shutil.copy2(
                manifest_path,
                reports / manifest_path.name,
            )

    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--remote-size", required=True, type=int)
    parser.add_argument("--local-archive", type=Path)
    parser.add_argument("--transport", default="ftp_mte")
    parser.add_argument("--transport-url")
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("work"),
    )
    args = parser.parse_args()

    summary = process_part(
        year=args.year,
        filename=args.filename,
        key=args.key,
        remote_size=args.remote_size,
        work_root=args.work_root,
        local_archive=args.local_archive,
        transport=args.transport,
        transport_url=args.transport_url,
    )
    print(summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
