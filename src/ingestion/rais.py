from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from ftplib import FTP
from pathlib import Path

from src.ingestion.manifest import build_manifest, write_manifest

FTP_HOST = "ftp.mtps.gov.br"
BASE_DIR = "pdet/microdados/RAIS"
VALID_DATASETS = {"vinculos", "estabelecimentos"}


@dataclass(frozen=True)
class RaisRemoteFile:
    year: int
    dataset: str
    filename: str

    @property
    def remote_dir(self) -> str:
        return f"{BASE_DIR}/{self.year}"

    @property
    def url(self) -> str:
        return f"ftp://{FTP_HOST}/{self.remote_dir}/{self.filename}"


def validate_year(year: int) -> None:
    if year < 1985 or year > 2100:
        raise ValueError("Ano RAIS inválido.")


def classify_filename(filename: str) -> str | None:
    upper = filename.upper()
    if not upper.endswith(".7Z"):
        return None
    if "ESTAB" in upper:
        return "estabelecimentos"
    if "VINC" in upper:
        return "vinculos"
    return None


def select_remote_files(
    year: int,
    filenames: list[str],
    *,
    dataset: str = "vinculos",
) -> list[RaisRemoteFile]:
    validate_year(year)
    normalized = dataset.strip().lower()
    if normalized not in VALID_DATASETS:
        raise ValueError(f"Dataset RAIS inválido: {dataset}")

    selected = [
        RaisRemoteFile(year=year, dataset=normalized, filename=filename)
        for filename in filenames
        if classify_filename(filename) == normalized
    ]
    return sorted(selected, key=lambda item: item.filename.upper())


def discover_files(
    year: int,
    *,
    dataset: str = "vinculos",
    host: str = FTP_HOST,
    timeout: int = 60,
) -> list[RaisRemoteFile]:
    validate_year(year)
    remote_dir = f"{BASE_DIR}/{year}"

    with FTP(host=host, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(remote_dir)
        filenames = ftp.nlst()

    return select_remote_files(year, filenames, dataset=dataset)


def download_file(
    remote: RaisRemoteFile,
    destination_dir: Path,
    *,
    host: str = FTP_HOST,
    timeout: int = 300,
) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / remote.filename
    temporary = destination.with_suffix(destination.suffix + ".part")

    with FTP(host=host, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(remote.remote_dir)
        with temporary.open("wb") as target:
            ftp.retrbinary(f"RETR {remote.filename}", target.write)

    if temporary.stat().st_size <= 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Download RAIS vazio: {remote.filename}")

    temporary.replace(destination)
    return destination


def download_year(
    year: int,
    destination_dir: Path,
    *,
    dataset: str = "vinculos",
) -> list[Path]:
    remotes = discover_files(year, dataset=dataset)
    if not remotes:
        raise RuntimeError(
            f"Nenhum arquivo RAIS {dataset} encontrado para {year}."
        )

    return [
        download_file(remote, destination_dir)
        for remote in remotes
    ]


def write_download_manifest(
    year: int,
    files: list[Path],
    destination: Path,
    *,
    dataset: str = "vinculos",
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    for path in files:
        remote = RaisRemoteFile(
            year=year,
            dataset=dataset,
            filename=path.name,
        )
        manifest = build_manifest(
            path,
            "rais_mte",
            str(year),
            transport="ftp_mte",
            source_url=remote.url,
        )
        manifest_path = path.with_suffix(path.suffix + ".manifest.json")
        write_manifest(manifest, manifest_path)
        entries.append(
            {
                **asdict(manifest),
                "path": path.name,
                "manifest": manifest_path.name,
                "dataset": dataset,
            }
        )

    destination.write_text(
        json.dumps(
            {
                "source": "RAIS / Ministério do Trabalho e Emprego",
                "year": year,
                "dataset": dataset,
                "concept": "estoque anual de vínculos formais em 31/12",
                "transport": "ftp_mte",
                "files": entries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
