from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.api.main import app


def export_openapi(destination: Path) -> None:
    payload = app.openapi()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta o contrato OpenAPI versionado da aplicação."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/openapi.json"),
    )
    args = parser.parse_args()
    export_openapi(args.output)


if __name__ == "__main__":
    main()
