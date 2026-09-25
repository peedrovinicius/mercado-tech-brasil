from __future__ import annotations

from pathlib import Path


def extract_7z(archive_path: Path, destination_dir: Path) -> list[Path]:
    try:
        import py7zr
    except ImportError as exc:
        raise RuntimeError(
            "py7zr não está instalado. Execute `pip install -e .`."
        ) from exc

    destination_dir.mkdir(parents=True, exist_ok=True)

    with py7zr.SevenZipFile(archive_path, mode="r") as archive:
        names = archive.getnames()
        archive.extractall(destination_dir)

    return [destination_dir / name for name in names]
