from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from ftplib import FTP, all_errors, error_perm
from pathlib import Path

from src.ingestion.archive import extract_7z
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


def remote_file_size(
    remote: RaisRemoteFile,
    *,
    host: str = FTP_HOST,
    timeout: int = 60,
) -> int | None:
    with FTP(host=host, timeout=timeout) as ftp:
        ftp.login()
        ftp.cwd(remote.remote_dir)
        ftp.voidcmd("TYPE I")
        try:
            size = ftp.size(remote.filename)
        except error_perm:
            return None
    return int(size) if size is not None else None


def select_smallest_remote_file(
    remotes: list[RaisRemoteFile],
    sizes: dict[str, int | None],
    *,
    exclude_residual: bool = True,
) -> RaisRemoteFile:
    if not remotes:
        raise ValueError("Nenhum arquivo RAIS disponível para seleção.")

    candidates = remotes
    if exclude_residual:
        regular = [
            item
            for item in remotes
            if "_NI." not in item.filename.upper()
        ]
        if regular:
            candidates = regular

    known = [
        item
        for item in candidates
        if isinstance(sizes.get(item.filename), int)
        and int(sizes[item.filename] or 0) > 0
    ]
    if known:
        return min(
            known,
            key=lambda item: (
                int(sizes[item.filename] or 0),
                item.filename.upper(),
            ),
        )

    return sorted(
        candidates,
        key=lambda item: item.filename.upper(),
    )[0]


def download_file(
    remote: RaisRemoteFile,
    destination_dir: Path,
    *,
    host: str = FTP_HOST,
    timeout: int = 300,
    max_attempts: int = 5,
) -> Path:
    if max_attempts < 1 or max_attempts > 10:
        raise ValueError("max_attempts deve estar entre 1 e 10.")

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / remote.filename
    temporary = destination.with_suffix(destination.suffix + ".part")
    last_error: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        offset = temporary.stat().st_size if temporary.exists() else 0

        try:
            with FTP(host=host, timeout=timeout) as ftp:
                ftp.login()
                ftp.cwd(remote.remote_dir)
                ftp.voidcmd("TYPE I")

                try:
                    remote_size = ftp.size(remote.filename)
                except error_perm:
                    remote_size = None

                if remote_size is not None and offset > remote_size:
                    temporary.unlink(missing_ok=True)
                    offset = 0

                if remote_size is not None and offset == remote_size and offset > 0:
                    temporary.replace(destination)
                    return destination

                mode = "ab" if offset else "wb"
                with temporary.open(mode) as target:
                    ftp.retrbinary(
                        f"RETR {remote.filename}",
                        target.write,
                        blocksize=1024 * 1024,
                        rest=offset if offset else None,
                    )

            downloaded_size = temporary.stat().st_size
            if downloaded_size <= 0:
                last_error = RuntimeError(
                    f"Download RAIS vazio: {remote.filename}"
                )
            elif remote_size is not None and downloaded_size != remote_size:
                last_error = RuntimeError(
                    "Download RAIS incompleto: "
                    f"{remote.filename} bytes={downloaded_size}/{remote_size}"
                )
            else:
                temporary.replace(destination)
                return destination

        except error_perm as exc:
            last_error = exc
            if offset:
                temporary.unlink(missing_ok=True)
        except all_errors as exc:
            last_error = exc

        if attempt < max_attempts:
            time.sleep(min(2 ** (attempt - 1), 8))

    partial_size = temporary.stat().st_size if temporary.exists() else 0
    raise RuntimeError(
        f"Falha ao baixar RAIS após {max_attempts} tentativas: "
        f"{remote.filename}; bytes_parciais={partial_size}"
    ) from last_error


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



def extract_year(
    year: int,
    archive_dir: Path,
    extracted_dir: Path,
) -> list[Path]:
    validate_year(year)
    archives = sorted(archive_dir.glob("*.7z"))
    if not archives:
        raise FileNotFoundError(
            f"Nenhum arquivo RAIS .7z encontrado em {archive_dir}"
        )

    metadata_by_archive: dict[str, dict[str, object]] = {}
    manifest_path = archive_dir / "download-manifest.json"
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata_by_archive = {
            str(item.get("path") or ""): item
            for item in payload.get("files", [])
            if isinstance(item, dict)
        }

    extracted_files: list[Path] = []
    for archive in archives:
        metadata = metadata_by_archive.get(archive.name, {})
        source_url = metadata.get("source_url")
        transport = metadata.get("transport")

        for path in extract_7z(archive, extracted_dir):
            if not path.is_file():
                continue

            file_manifest = build_manifest(
                path,
                "rais_mte",
                str(year),
                transport=str(transport) if transport else None,
                source_url=str(source_url) if source_url else None,
            )
            write_manifest(
                file_manifest,
                path.with_suffix(path.suffix + ".manifest.json"),
            )
            extracted_files.append(path)

    return sorted(extracted_files)
