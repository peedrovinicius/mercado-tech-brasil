from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from ftplib import all_errors
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.ingestion.ftp_caged import (
    BASE_DIR,
    FTP_HOST,
    VALID_FILE_TYPES,
    download_month,
    validate_yearmonth,
)

HF_BASE = "https://huggingface.co/datasets/alexsandroprado/caged/resolve/main"
HF_REPOSITORY = "https://huggingface.co/datasets/alexsandroprado/caged"
FTP_DOWNLOAD_ERRORS = all_errors + (RuntimeError, ValueError)


@dataclass(frozen=True)
class HttpsRemoteFile:
    yearmonth: str
    kind: str
    filename: str
    url: str


@dataclass(frozen=True)
class DownloadArtifact:
    path: Path
    kind: str
    transport: str
    url: str


def build_https_remote(yearmonth: str, kind: str) -> HttpsRemoteFile:
    validate_yearmonth(yearmonth)
    normalized = kind.upper().strip()
    if normalized not in VALID_FILE_TYPES:
        raise ValueError(f"Tipo inválido: {normalized}")

    filename = f"CAGED{normalized}{yearmonth}.7z"
    year = yearmonth[:4]
    url = f"{HF_BASE}/NOVO_CAGED/{year}/{yearmonth}/{filename}"
    return HttpsRemoteFile(
        yearmonth=yearmonth,
        kind=normalized,
        filename=filename,
        url=url,
    )


def download_https_file(
    remote: HttpsRemoteFile,
    destination_dir: Path,
    *,
    timeout: int = 300,
    attempts: int = 3,
) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / remote.filename
    temporary = destination.with_suffix(destination.suffix + ".part")

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(
                remote.url,
                headers={"User-Agent": "mercado-tech-brasil/0.13"},
            )
            with urlopen(request, timeout=timeout) as response, temporary.open("wb") as target:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)

            if temporary.stat().st_size <= 0:
                raise RuntimeError(f"Download vazio: {remote.url}")

            temporary.replace(destination)
            return destination
        except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
            last_error = exc
            if temporary.exists():
                temporary.unlink()
            if attempt < attempts:
                time.sleep(2 * attempt)

    raise RuntimeError(
        f"Falha no download HTTPS de {remote.filename} após {attempts} tentativas."
    ) from last_error


def download_month_https(
    yearmonth: str,
    destination_dir: Path,
    file_types: Iterable[str] = ("MOV", "FOR", "EXC"),
) -> list[DownloadArtifact]:
    artifacts: list[DownloadArtifact] = []
    for kind in file_types:
        remote = build_https_remote(yearmonth, kind)
        path = download_https_file(remote, destination_dir)
        artifacts.append(
            DownloadArtifact(
                path=path,
                kind=remote.kind,
                transport="https_huggingface_mirror",
                url=remote.url,
            )
        )
    return artifacts


def write_download_manifest(
    artifacts: Iterable[DownloadArtifact],
    destination: Path,
) -> None:
    payload = {
        "official_source": "Novo CAGED / Ministério do Trabalho e Emprego",
        "transport_repository": HF_REPOSITORY,
        "files": [
            {
                **asdict(item),
                "path": item.path.name,
            }
            for item in artifacts
        ],
    }
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )



def download_month_resilient(
    yearmonth: str,
    destination_dir: Path,
    file_types: Iterable[str] = ("MOV", "FOR", "EXC"),
) -> list[DownloadArtifact]:
    requested = tuple(kind.upper().strip() for kind in file_types)

    try:
        paths = download_month(
            yearmonth,
            destination_dir,
            file_types=requested,
        )
        artifacts = []
        for path in paths:
            upper = path.name.upper()
            kind = next(
                candidate
                for candidate in requested
                if f"CAGED{candidate}" in upper
            )
            remote_dir = f"{BASE_DIR}/{yearmonth[:4]}/{yearmonth}"
            artifacts.append(
                DownloadArtifact(
                    path=path,
                    kind=kind,
                    transport="ftp_mte",
                    url=f"ftp://{FTP_HOST}/{remote_dir}/{path.name}",
                )
            )
        return artifacts
    except FTP_DOWNLOAD_ERRORS as ftp_error:
        try:
            return download_month_https(
                yearmonth,
                destination_dir,
                file_types=requested,
            )
        except RuntimeError as https_error:
            raise RuntimeError(
                "Falha nos dois transportes de microdados: FTP do MTE e HTTPS alternativo."
            ) from ExceptionGroup(
                "Erros de transporte",
                [ftp_error, https_error],
            )
