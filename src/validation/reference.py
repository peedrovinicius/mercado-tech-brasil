from __future__ import annotations

from pathlib import Path
import json


def load_reference(reference_path: Path, yearmonth: str) -> dict | None:
    payload = json.loads(reference_path.read_text(encoding="utf-8"))
    return payload.get(yearmonth)


def validate_reference_integrity(reference: dict) -> None:
    admissions = int(reference["admissoes"])
    dismissals = int(reference["desligamentos"])
    balance = int(reference["saldo"])
    if admissions - dismissals != balance:
        raise ValueError(
            "Referência oficial inconsistente: admissões - desligamentos != saldo"
        )
