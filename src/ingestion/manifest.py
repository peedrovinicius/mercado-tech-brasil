from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class FileManifest:
    source: str
    competence: str
    original_name: str
    size_bytes: int
    sha256: str
    ingested_at_utc: str
    transport: str | None = None
    source_url: str | None = None


def build_manifest(
    path: Path,
    source: str,
    competence: str,
    *,
    transport: str | None = None,
    source_url: str | None = None,
) -> FileManifest:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return FileManifest(
        source=source,
        competence=competence,
        original_name=path.name,
        size_bytes=path.stat().st_size,
        sha256=digest.hexdigest(),
        ingested_at_utc=datetime.now(UTC).isoformat(),
        transport=transport,
        source_url=source_url,
    )


def write_manifest(manifest: FileManifest, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                key: value
                for key, value in asdict(manifest).items()
                if value is not None
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
