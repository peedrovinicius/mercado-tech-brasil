from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from src.ingestion.archive import extract_7z
from src.ingestion.manifest import build_manifest, write_manifest


VALID_KINDS = {"MOV", "FOR", "EXC"}


@dataclass(frozen=True)
class LocalIngestResult:
    source_path: Path
    bronze_file: Path
    extracted_files: tuple[Path, ...]
    manifest_files: tuple[Path, ...]


def _validate_kind(kind: str) -> str:
    normalized = kind.upper().strip()
    if normalized not in VALID_KINDS:
        raise ValueError(f"kind deve ser um de {sorted(VALID_KINDS)}")
    return normalized


def _safe_copy(source: Path, destination: Path) -> None:
    if destination.exists():
        if source.read_bytes() == destination.read_bytes():
            return
        raise FileExistsError(
            f"Já existe um arquivo diferente no destino Bronze: {destination}"
        )
    shutil.copy2(source, destination)


def ingest_local_file(
    source: Path,
    *,
    yearmonth: str,
    kind: str,
    bronze_root: Path,
) -> LocalIngestResult:
    """Ingere um arquivo local mantendo o original imutável na Bronze.

    Aceita TXT oficial já extraído ou arquivo .7z baixado manualmente.
    A origem local é útil quando o ambiente não possui acesso FTP.
    """
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)

    kind = _validate_kind(kind)
    suffix = source.suffix.lower()
    if suffix not in {".txt", ".7z"}:
        raise ValueError("A ingestão local aceita apenas .txt ou .7z")

    month_dir = bronze_root / yearmonth
    archive_dir = month_dir / "archives"
    extracted_dir = month_dir / "extracted"
    archive_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)

    if suffix == ".7z":
        bronze_file = archive_dir / source.name
        _safe_copy(source, bronze_file)
        extracted = tuple(extract_7z(bronze_file, extracted_dir))
    else:
        bronze_file = extracted_dir / source.name
        _safe_copy(source, bronze_file)
        extracted = (bronze_file,)

    manifest_files: list[Path] = []
    for file in extracted:
        if not file.is_file():
            continue
        manifest = build_manifest(
            file,
            source=f"novo_caged_{kind.lower()}_local",
            competence=yearmonth,
        )
        manifest_path = file.with_suffix(file.suffix + ".manifest.json")
        write_manifest(manifest, manifest_path)
        manifest_files.append(manifest_path)

    return LocalIngestResult(
        source_path=source,
        bronze_file=bronze_file,
        extracted_files=tuple(file for file in extracted if file.is_file()),
        manifest_files=tuple(manifest_files),
    )
