from __future__ import annotations

VALID_UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}


def valid_uf(value: str | None) -> bool:
    return value in VALID_UFS


def valid_cbo(value: str | None) -> bool:
    return bool(value) and value.isdigit() and len(value) >= 4


def valid_salary(value: float | None) -> bool:
    return value is None or value >= 0
