from __future__ import annotations

import argparse
import json
import os
import re
from ftplib import FTP
from pathlib import Path

FTP_HOST = "ftp.mtps.gov.br"
BASE_DIR = "pdet/microdados/RAIS"
EXPECTED_FILES = 7
MAX_TOTAL_BYTES = 8_000_000_000
MAX_FILE_BYTES = 3_000_000_000


def discover(year: int) -> dict[str, object]:
    if year != 2025:
        raise ValueError("Este executor integral está travado na RAIS 2025.")

    remote_dir = f"{BASE_DIR}/{year}"
    with FTP(host=FTP_HOST, timeout=60) as ftp:
        ftp.login()
        ftp.cwd(remote_dir)
        names = sorted(
            name
            for name in ftp.nlst()
            if name.upper().endswith(".7Z")
            and "VINC" in name.upper()
            and "ESTAB" not in name.upper()
        )
        ftp.voidcmd("TYPE I")

        files = []
        for name in names:
            size = ftp.size(name)
            if size is None or size <= 0:
                raise RuntimeError(f"Tamanho remoto inválido: {name}")
            key = re.sub(
                r"[^a-z0-9]+",
                "-",
                name.lower().removesuffix(".7z"),
            ).strip("-")
            files.append(
                {
                    "filename": name,
                    "key": key,
                    "size": int(size),
                }
            )

    if len(files) != EXPECTED_FILES:
        raise RuntimeError(
            f"Esperados {EXPECTED_FILES} arquivos de vínculos; "
            f"encontrados {len(files)}."
        )

    total = sum(int(item["size"]) for item in files)
    largest = max(int(item["size"]) for item in files)
    if total > MAX_TOTAL_BYTES:
        raise RuntimeError(
            f"Volume compactado acima do limite: {total} bytes."
        )
    if largest > MAX_FILE_BYTES:
        raise RuntimeError(
            f"Arquivo regional acima do limite: {largest} bytes."
        )

    return {
        "year": year,
        "file_count": len(files),
        "total_bytes": total,
        "largest_file_bytes": largest,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("rais-discovery-2025.json"),
    )
    args = parser.parse_args()

    payload = discover(args.year)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    matrix = json.dumps(
        {"include": payload["files"]},
        separators=(",", ":"),
    )
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"matrix={matrix}\n")
            handle.write(f"total_bytes={payload['total_bytes']}\n")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
