from pathlib import Path

from src.validation.official_reference import (
    load_official_reference,
    reference_is_valid,
    validate_official_reference,
)


def test_july_2026_official_reference_closes_exactly():
    reference = load_official_reference(Path("config/official_reference_202607.json"))
    checks = validate_official_reference(reference)

    assert reference_is_valid(reference)
    assert all(check.passed for check in checks)
    assert reference["national"]["admissions"] == 2262888
    assert reference["national"]["dismissals"] == 2204320
    assert reference["national"]["balance"] == 58568
    assert reference["ufs"]["CE"]["balance"] == 4181


def test_ceara_reference_contains_official_salary_mean():
    reference = load_official_reference(Path("config/official_reference_202607.json"))
    assert reference["ufs"]["CE"]["salary_mean_admission_brl"] == 2173.94
