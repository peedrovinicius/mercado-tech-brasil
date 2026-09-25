from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from ftplib import FTP
from pathlib import Path

FTP_HOST = "ftp.mtps.gov.br"
BASE_DIR = "pdet/microdados/NOVO CAGED"
VALID_FILE_TYPES = {"MOV", "FOR", "EXC"}


@dataclass(frozen=True)
class RemoteFile:
    yearmonth: str
    kind: str
    filename: str


def validate_yearmonth(yearmonth: str) -> None:
    if len(yearmonth) != 6 or not yearmonth.isdigit():
        raise ValueError("yearmonth deve estar no formato AAAAMM")
    month = int(yearmonth[4:])
    if month < 1 or month > 12:
        raise ValueError("Mês inválido em yearmonth")


def discover_files(
    yearmonth: str,
    file_types: Iterable[str] = ("MOV", "FOR", "EXC"),
    *,
    host: str = FTP_HOST,
    timeout: int = 60,
) -> list[RemoteFile]:
    validate_yearmonth(yearmonth)
    requested = {item.upper() for item in file_types}

    invalid = requested - VALID_FILE_TYPES
    if invalid:
        raise ValueError(f"Tipos inválidos: {sorted(invalid)}")

    year = yearmonth[:4]
    remote_dir = f"{BASE_DIR}/{year}/{yearmonth}"

    with FTP(host=host, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(remote_dir)
        filenames = ftp.nlst()

    result: list[RemoteFile] = []
    for filename in filenames:
        upper = filename.upper()
        if not upper.endswith(".7Z"):
            continue
        for kind in requested:
            if f"CAGED{kind}" in upper:
                result.append(RemoteFile(yearmonth, kind, filename))
                break

    return sorted(result, key=lambda item: (item.kind, item.filename))


def download_file(
    remote: RemoteFile,
    destination_dir: Path,
    *,
    host: str = FTP_HOST,
    timeout: int = 120,
) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / remote.filename
    temp = destination.with_suffix(destination.suffix + ".part")

    remote_dir = (
        f"{BASE_DIR}/{remote.yearmonth[:4]}/{remote.yearmonth}"
    )

    with FTP(host=host, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(remote_dir)
        with temp.open("wb") as file:
            ftp.retrbinary(f"RETR {remote.filename}", file.write)

    temp.replace(destination)
    return destination


def download_month(
    yearmonth: str,
    destination_dir: Path,
    file_types: Iterable[str] = ("MOV", "FOR", "EXC"),
) -> list[Path]:
    files = discover_files(yearmonth, file_types)
    if not files:
        raise RuntimeError(f"Nenhum arquivo .7z encontrado para {yearmonth}")

    downloaded: list[Path] = []
    for remote in files:
        downloaded.append(download_file(remote, destination_dir))
    return downloaded
