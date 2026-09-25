from pathlib import Path

from src.validation.reference import (
    load_reference,
    validate_reference_integrity,
)


def test_official_july_2026_reference_is_internally_consistent():
    path = Path("config/reference_totals.json")
    reference = load_reference(path, "202607")
    assert reference is not None
    validate_reference_integrity(reference)
    assert reference["admissoes"] - reference["desligamentos"] == reference["saldo"]
