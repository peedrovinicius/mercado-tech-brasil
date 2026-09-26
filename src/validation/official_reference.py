from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

UF_BY_REGION = {
    "Norte": ("RO", "AC", "AM", "RR", "PA", "AP", "TO"),
    "Nordeste": ("MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"),
    "Sudeste": ("MG", "ES", "RJ", "SP"),
    "Sul": ("PR", "SC", "RS"),
    "Centro-Oeste": ("MS", "MT", "GO", "DF"),
}


@dataclass(frozen=True)
class ReferenceCheck:
    id: str
    passed: bool
    message: str


def load_official_reference(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _arithmetic_ok(item: dict) -> bool:
    return int(item["admissions"]) - int(item["dismissals"]) == int(item["balance"])


def validate_official_reference(reference: dict) -> tuple[ReferenceCheck, ...]:
    checks: list[ReferenceCheck] = []

    national = reference["national"]
    checks.append(
        ReferenceCheck(
            id="national_arithmetic",
            passed=_arithmetic_ok(national),
            message="Total nacional: admissões - desligamentos = saldo.",
        )
    )

    ufs = reference["ufs"]
    invalid_ufs = sorted(uf for uf, item in ufs.items() if not _arithmetic_ok(item))
    checks.append(
        ReferenceCheck(
            id="uf_arithmetic",
            passed=not invalid_ufs,
            message=(
                "Todas as UFs possuem aritmética consistente."
                if not invalid_ufs
                else f"UFs inconsistentes: {', '.join(invalid_ufs)}"
            ),
        )
    )

    regions = reference["regions"]
    invalid_regions = sorted(
        region for region, item in regions.items() if not _arithmetic_ok(item)
    )
    checks.append(
        ReferenceCheck(
            id="region_arithmetic",
            passed=not invalid_regions,
            message=(
                "Todas as regiões possuem aritmética consistente."
                if not invalid_regions
                else f"Regiões inconsistentes: {', '.join(invalid_regions)}"
            ),
        )
    )

    region_mismatches: list[str] = []
    for region, uf_codes in UF_BY_REGION.items():
        calculated = {
            metric: sum(int(ufs[uf][metric]) for uf in uf_codes)
            for metric in ("admissions", "dismissals", "balance")
        }
        published = {
            metric: int(regions[region][metric])
            for metric in ("admissions", "dismissals", "balance")
        }
        if calculated != published:
            region_mismatches.append(region)

    checks.append(
        ReferenceCheck(
            id="regions_equal_sum_of_ufs",
            passed=not region_mismatches,
            message=(
                "Os totais regionais são exatamente a soma das respectivas UFs."
                if not region_mismatches
                else f"Regiões divergentes: {', '.join(region_mismatches)}"
            ),
        )
    )

    non_identified = reference["non_identified"]
    uf_plus_unidentified = {
        metric: (
            sum(int(item[metric]) for item in ufs.values())
            + int(non_identified[metric])
        )
        for metric in ("admissions", "dismissals", "balance")
    }
    national_values = {
        metric: int(national[metric])
        for metric in ("admissions", "dismissals", "balance")
    }
    checks.append(
        ReferenceCheck(
            id="national_equals_ufs_plus_unidentified",
            passed=uf_plus_unidentified == national_values,
            message=(
                "Total nacional fecha com 27 UFs + registros não identificados."
                if uf_plus_unidentified == national_values
                else "Total nacional não fecha com 27 UFs + não identificados."
            ),
        )
    )

    salary = reference["salary_methodology"]
    expected_min = round(
        float(salary["minimum_wage_brl"]) * float(salary["minimum_multiple"]),
        2,
    )
    expected_max = round(
        float(salary["minimum_wage_brl"]) * float(salary["maximum_multiple"]),
        2,
    )
    salary_bounds_ok = (
        expected_min == float(salary["minimum_salary_brl"])
        and expected_max == float(salary["maximum_salary_brl"])
        and bool(salary["exclude_intermittent"])
    )
    checks.append(
        ReferenceCheck(
            id="salary_methodology",
            passed=salary_bounds_ok,
            message=(
                "Limites salariais e exclusão de intermitentes estão consistentes."
                if salary_bounds_ok
                else "Configuração da metodologia salarial está inconsistente."
            ),
        )
    )

    return tuple(checks)


def reference_is_valid(reference: dict) -> bool:
    return all(check.passed for check in validate_official_reference(reference))
