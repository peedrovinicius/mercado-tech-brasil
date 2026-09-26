from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import py7zr

CONFIG_PATH = Path("config/rais_transport_mirror.json")
TARGETS = {
    "NORTE": {
        "filename": "RAIS_VINC_PUB_NORTE.7z",
        "official_active": 3869191,
    }
}


def _download(url: str, destination: Path, expected_size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--show-error",
            "--retry",
            "8",
            "--retry-delay",
            "2",
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
        ],
        check=True,
    )
    size = destination.stat().st_size
    if size != expected_size:
        raise RuntimeError(
            f"Tamanho divergente: {destination.name} {size}/{expected_size}"
        )


def _parse_number(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def diagnose(region: str, work: Path) -> dict[str, object]:
    target = TARGETS[region]
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    filename = target["filename"]
    official_active = int(target["official_active"])

    discovery = config["official_discovery"]["files"]
    source = next(
        item for item in discovery
        if item["filename"] == filename
    )
    expected_size = int(source["size_bytes"])

    dataset = str(config["mirror_dataset"])
    prefix = str(config["mirror_path_prefix"]).strip("/")
    refs = [
        str(config["mirror_commit"]),
        str(config.get("mirror_fallback_ref") or "main"),
    ]

    archive = work / filename
    used_url = None
    errors: list[str] = []

    for ref in refs:
        url = (
            f"https://huggingface.co/datasets/{dataset}/resolve/{ref}/"
            f"{prefix}/{filename}?download=true"
        )
        archive.unlink(missing_ok=True)
        try:
            _download(url, archive, expected_size)
        except Exception as exc:
            errors.append(f"{ref}: {exc}")
            continue
        used_url = url
        break

    if used_url is None:
        raise RuntimeError("Falha no espelho: " + " | ".join(errors))

    extracted = work / "extracted"
    shutil.rmtree(extracted, ignore_errors=True)
    extracted.mkdir(parents=True, exist_ok=True)

    with py7zr.SevenZipFile(archive, mode="r") as handle:
        handle.extractall(path=extracted)

    files = [
        path for path in extracted.rglob("*")
        if path.is_file() and path.suffix.lower() in {".comt", ".csv", ".txt"}
    ]
    if len(files) != 1:
        raise RuntimeError(
            f"Esperado um arquivo tabular; encontrados {len(files)}."
        )

    source_file = files[0]
    abandoned_counter: Counter[str] = Counter()
    active_total = 0
    active_abandoned_zero = 0
    active_abandoned_not_one = 0
    active_rem_mean_positive = 0
    active_rem_dec_positive = 0
    active_abandoned_zero_rem_mean_positive = 0
    active_abandoned_zero_rem_dec_positive = 0

    with source_file.open(
        "r",
        encoding="latin-1",
        newline="",
        errors="strict",
    ) as handle:
        reader = csv.DictReader(handle, delimiter=",")
        required = {
            "Ind Vínculo Ativo 31/12 - Código",
            "Ind Vínculo Abandonado - Código",
            "Vl Rem Média Nom",
            "Vl Rem Dezembro Nom",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(
                "Colunas ausentes: " + ", ".join(sorted(missing))
            )

        for row in reader:
            active = str(
                row.get("Ind Vínculo Ativo 31/12 - Código") or ""
            ).strip()
            if active != "1":
                continue

            active_total += 1
            abandoned = str(
                row.get("Ind Vínculo Abandonado - Código") or ""
            ).strip()
            abandoned_counter[abandoned] += 1

            rem_mean = _parse_number(row.get("Vl Rem Média Nom"))
            rem_dec = _parse_number(row.get("Vl Rem Dezembro Nom"))

            if abandoned == "0":
                active_abandoned_zero += 1
            if abandoned != "1":
                active_abandoned_not_one += 1
            if rem_mean is not None and rem_mean > 0:
                active_rem_mean_positive += 1
            if rem_dec is not None and rem_dec > 0:
                active_rem_dec_positive += 1
            if (
                abandoned == "0"
                and rem_mean is not None
                and rem_mean > 0
            ):
                active_abandoned_zero_rem_mean_positive += 1
            if (
                abandoned == "0"
                and rem_dec is not None
                and rem_dec > 0
            ):
                active_abandoned_zero_rem_dec_positive += 1

    candidates = {
        "active_total": active_total,
        "active_abandoned_zero": active_abandoned_zero,
        "active_abandoned_not_one": active_abandoned_not_one,
        "active_rem_mean_positive": active_rem_mean_positive,
        "active_rem_dec_positive": active_rem_dec_positive,
        "active_abandoned_zero_rem_mean_positive": (
            active_abandoned_zero_rem_mean_positive
        ),
        "active_abandoned_zero_rem_dec_positive": (
            active_abandoned_zero_rem_dec_positive
        ),
    }

    exact_matches = [
        name
        for name, value in candidates.items()
        if value == official_active
    ]

    result = {
        "region": region,
        "archive": filename,
        "transport_url": used_url,
        "official_active": official_active,
        "raw_active": active_total,
        "raw_minus_official": active_total - official_active,
        "abandoned_values_among_active": dict(
            sorted(abandoned_counter.items())
        ),
        "candidates": candidates,
        "exact_matches": exact_matches,
    }

    archive.unlink(missing_ok=True)
    shutil.rmtree(extracted, ignore_errors=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--region",
        choices=sorted(TARGETS),
        default="NORTE",
    )
    parser.add_argument(
        "--work",
        type=Path,
        default=Path("work/rais-stock-diagnostic"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("rais-stock-diagnostic.json"),
    )
    args = parser.parse_args()

    args.work.mkdir(parents=True, exist_ok=True)
    result = diagnose(args.region, args.work)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
