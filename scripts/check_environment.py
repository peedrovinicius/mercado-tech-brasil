from __future__ import annotations

import importlib.util
import sys

REQUIRED = {
    "fastapi": "API",
    "polars": "ETL",
    "py7zr": "extração .7z",
    "yaml": "configuração YAML",
    "sqlalchemy": "PostgreSQL",
}

missing = []
print(f"Python: {sys.version.split()[0]}")

for package, purpose in REQUIRED.items():
    found = importlib.util.find_spec(package) is not None
    print(f"{package:<12} {'OK' if found else 'FALTANDO':<9} {purpose}")
    if not found:
        missing.append(package)

if missing:
    print("\\nDependências ausentes. Execute: pip install -e \".[dev]\"")
    raise SystemExit(1)

print("\\nAmbiente pronto.")
