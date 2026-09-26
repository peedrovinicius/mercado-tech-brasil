from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("rais-full-run-summary.json"),
    )
    args = parser.parse_args()

    year = args.year
    payload = {
        "year": year,
        "quality": _load(
            Path(f"data/silver/rais_quality_{year}.json")
        ),
        "reconciliation": _load(
            Path(f"data/silver/rais_reconciliation_{year}.json")
        ),
        "overview": _load(
            Path(f"data/gold/rais-overview-{year}.json")
        ),
        "publication_gate": _load(
            Path(f"data/gold/rais-publication-gate-{year}.json")
        ),
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
