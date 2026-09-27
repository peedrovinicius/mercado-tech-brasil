from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RaisRegionalCheck:
    archive: str
    label: str
    expected_stock: int
    observed_stock: int
    raw_active: int
    abandoned_active: int
    difference: int
    matched: bool


@dataclass(frozen=True)
class RaisRegionalReconciliationResult:
    year: int
    expected_national_stock: int
    observed_national_stock: int
    difference: int
    group_count: int
    regional_reconciled: bool
    source: str
    source_url: str
    source_page: int | None
    groups: tuple[RaisRegionalCheck, ...]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def _part_summaries(parts_root: Path) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for path in sorted(parts_root.rglob("part-summary.json")):
        payload = _read_json(path)
        archive = str(payload.get("archive") or "")
        if not archive:
            raise ValueError(f"Resumo regional sem arquivo de origem: {path}")
        if archive in summaries:
            raise ValueError(f"Resumo regional duplicado: {archive}")
        summaries[archive] = payload
    return summaries


def evaluate_rais_regional_reconciliation(
    *,
    year: int,
    parts_root: Path,
    reference_path: Path,
) -> RaisRegionalReconciliationResult:
    references = _read_json(reference_path)
    reference = references.get(str(year))
    if not isinstance(reference, dict):
        raise TypeError(f"Referência regional RAIS ausente para {year}.")

    expected_groups = reference.get("groups")
    if not isinstance(expected_groups, dict) or not expected_groups:
        raise ValueError("Referência regional RAIS sem grupos.")

    summaries = _part_summaries(parts_root)
    if set(summaries) != set(expected_groups):
        missing = sorted(set(expected_groups) - set(summaries))
        extra = sorted(set(summaries) - set(expected_groups))
        raise ValueError(
            "Partes regionais RAIS divergentes da referência. "
            f"ausentes={missing}; extras={extra}"
        )

    checks: list[RaisRegionalCheck] = []
    for archive in sorted(expected_groups):
        spec = expected_groups[archive]
        if not isinstance(spec, dict):
            raise TypeError(f"Referência regional inválida: {archive}")

        summary = summaries[archive]
        if int(summary.get("year") or 0) != year:
            raise ValueError(f"Ano regional divergente em {archive}.")

        expected = int(spec.get("expected_stock") or 0)
        observed = int(summary.get("rows_stock_eligible_source") or 0)
        raw_active = int(summary.get("rows_active_source") or 0)
        abandoned = int(summary.get("rows_abandoned_source") or 0)
        unknown_abandoned = int(summary.get("rows_unknown_abandoned_source") or 0)
        unknown_status = int(summary.get("rows_unknown_status_source") or 0)
        rejected = int(summary.get("rows_rejected") or 0)

        integrity_ok = (
            raw_active == observed + abandoned + unknown_abandoned
            and unknown_abandoned == 0
            and unknown_status == 0
            and rejected == 0
        )
        difference = observed - expected
        checks.append(
            RaisRegionalCheck(
                archive=archive,
                label=str(spec.get("label") or archive),
                expected_stock=expected,
                observed_stock=observed,
                raw_active=raw_active,
                abandoned_active=abandoned,
                difference=difference,
                matched=integrity_ok and difference == 0,
            )
        )

    expected_national = int(reference.get("national_active_links") or 0)
    observed_national = sum(item.observed_stock for item in checks)
    difference = observed_national - expected_national
    reconciled = (
        len(checks) == len(expected_groups)
        and all(item.matched for item in checks)
        and difference == 0
    )

    return RaisRegionalReconciliationResult(
        year=year,
        expected_national_stock=expected_national,
        observed_national_stock=observed_national,
        difference=difference,
        group_count=len(checks),
        regional_reconciled=reconciled,
        source=str(reference.get("source") or ""),
        source_url=str(reference.get("source_url") or ""),
        source_page=(
            int(reference["source_page"])
            if reference.get("source_page") is not None
            else None
        ),
        groups=tuple(checks),
    )


def write_rais_regional_reconciliation(
    result: RaisRegionalReconciliationResult,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["groups"] = [asdict(item) for item in result.groups]
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
