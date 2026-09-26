from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from scripts.rais_process_part import process_part

CONFIG_PATH = Path("config/rais_transport_mirror.json")


def _key(filename: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        filename.lower().removesuffix(".7z"),
    ).strip("-")


def _mirror_url(config: dict, filename: str) -> str:
    dataset = str(config["mirror_dataset"])
    commit = str(config["mirror_commit"])
    prefix = str(config["mirror_path_prefix"]).strip("/")
    return (
        f"https://huggingface.co/datasets/{dataset}/resolve/{commit}/"
        f"{prefix}/{filename}?download=true"
    )


def _download(url: str, destination: Path, expected_size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "curl",
        "-L",
        "--fail",
        "--show-error",
        "--retry",
        "5",
        "--retry-delay",
        "2",
        "--retry-all-errors",
        "--connect-timeout",
        "20",
        "--speed-limit",
        "1024",
        "--speed-time",
        "60",
        "-C",
        "-",
        "-o",
        str(destination),
        url,
    ]
    subprocess.run(command, check=True)

    actual_size = destination.stat().st_size
    if actual_size != expected_size:
        raise RuntimeError(
            f"Tamanho do espelho diverge do FTP oficial para "
            f"{destination.name}: {actual_size}/{expected_size}"
        )


def _cleanup_raw(part_dir: Path) -> None:
    archive_dir = part_dir / "archives"
    if archive_dir.exists():
        for pattern in ("*.7z", "*.part"):
            for path in archive_dir.glob(pattern):
                path.unlink(missing_ok=True)
    shutil.rmtree(part_dir / "extracted", ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("work/parts"),
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Nome de arquivo já processado que deve ser reutilizado.",
    )
    args = parser.parse_args()

    if args.year != 2025:
        raise SystemExit("Este retry de transporte está travado na RAIS 2025.")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    discovery = config.get("official_discovery") or {}
    files = discovery.get("files") or []
    if len(files) != 7:
        raise RuntimeError("Descoberta oficial versionada não possui sete arquivos.")

    skip = {str(value) for value in args.skip}
    pending = [
        item
        for item in files
        if str(item["filename"]) not in skip
    ]
    pending.sort(key=lambda item: int(item["size_bytes"]))

    download_dir = Path("work/mirror-downloads")
    completed: list[dict[str, object]] = []

    for item in pending:
        filename = str(item["filename"])
        expected_size = int(item["size_bytes"])
        key = _key(filename)
        url = _mirror_url(config, filename)
        local_archive = download_dir / filename

        print(
            f"mirror download: arquivo={filename} bytes={expected_size}"
        )
        _download(url, local_archive, expected_size)

        summary_path = process_part(
            year=args.year,
            filename=filename,
            key=key,
            remote_size=expected_size,
            work_root=args.work_root,
            local_archive=local_archive,
            transport="https_huggingface_mirror",
            transport_url=url,
        )
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        completed.append(summary)
        _cleanup_raw(args.work_root / key)

        print(
            f"mirror part complete: arquivo={filename} "
            f"rows={summary['rows_read']} tech={summary['rows_tech']}"
        )

    output = Path("work/mirror-retry-summary.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "year": args.year,
                "transport": "https_huggingface_mirror",
                "completed": completed,
                "skipped": sorted(skip),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
