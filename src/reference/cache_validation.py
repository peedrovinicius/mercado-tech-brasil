"""Validate versioned IBGE reference caches before offline CAGED audits.

A cache is only reusable if its source, year, coverage and internal consistency
match the expected official reference. Never generate missing values.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path


def verify_population_snapshot(path: Path, year: int) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("source") != "IBGE SIDRA"
        or str(payload.get("table")) != "6579"
        or str(payload.get("variable")) != "9324"
        or payload.get("reference_year") != year
        or payload.get("reference_date") != f"{year}-07-01"
    ):
        raise ValueError("Cache de população não corresponde ao IBGE 2026.")

    municipalities = payload.get("municipalities")
    if not isinstance(municipalities, dict) or len(municipalities) != 5571:
        raise ValueError("Cache populacional sem cobertura municipal completa.")

    prefixes = set()
    for code, population in municipalities.items():
        if (
            not isinstance(code, str)
            or len(code) != 7
            or not code.isdigit()
            or not isinstance(population, int)
            or isinstance(population, bool)
            or population <= 0
        ):
            raise ValueError(f"Cache populacional com linha inválida: {code}")
        prefixes.add(code[:6])
    if len(prefixes) != len(municipalities):
        raise ValueError("Códigos municipais incompatíveis com CAGED 6 dígitos.")
    return len(municipalities)


def verify_ipca_snapshot(
    path: Path,
    *,
    competence: str,
    base_competence: str,
) -> Decimal:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("source") != "IBGE SIDRA"
        or str(payload.get("table")) != "1737"
        or str(payload.get("variable")) != "2266"
        or payload.get("base_competence") != base_competence
    ):
        raise ValueError("Cache de IPCA não corresponde à tabela oficial IBGE.")

    indices = payload.get("indices")
    if not isinstance(indices, dict):
        raise TypeError("Índices IPCA ausentes.")
    for period in (competence, base_competence):
        if (
            len(period) != 6
            or not period.isdigit()
            or period not in indices
            or Decimal(str(indices[period])) <= 0
        ):
            raise ValueError(f"Índice IPCA ausente ou inválido: {period}")

    value = Decimal(str(indices[competence]))
    if competence == "202609":
        previous = Decimal(str(indices.get("202608", "0")))
        if previous != Decimal("7633.23") or value != Decimal("7695.82"):
            raise ValueError("Série IPCA de setembro 2026 mudou sem revisão.")
        monthly_rate = (value / previous - 1) * 100
        if monthly_rate.quantize(Decimal("0.01")) != Decimal("0.82"):
            raise ValueError("Índice IPCA não corresponde ao IPCA oficial 0,82%.")
        official_page = (
            payload.get("reference_sources") or {}
        ).get("202609")
        if official_page != "https://sidra.ibge.gov.br/tabela/1737":
            raise ValueError("Referência oficial IPCA de setembro ausente.")
    return value


def verify_audit_references(
    *,
    population_path: Path,
    ipca_path: Path,
    competence: str,
    base_competence: str,
) -> None:
    year = int(competence[:4])
    if year != 2026:
        raise ValueError("Reuso populacional validado somente para o ano 2026.")
    if date.fromisoformat(f"{year}-07-01") > date.today():
        raise ValueError("Referência populacional ainda não vigente.")
    count = verify_population_snapshot(population_path, year)
    index = verify_ipca_snapshot(
        ipca_path,
        competence=competence,
        base_competence=base_competence,
    )
    print(
        f"Cache oficial IBGE validado: população={year}, "
        f"municípios={count}, IPCA {competence}={index}"
    )
