from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RaisReconciliationResult:
    year: int
    expected_active: int
    observed_active: int
    difference: int
    source_partition_complete: bool
    unknown_status_rows: int
    year_mismatch_rows: int
    tech_rows: int
    reconciled: bool
    gold_ready: bool
    publication_ready: bool
    source: str
    source_url: str


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def evaluate_rais_reconciliation(
    *,
    year: int,
    quality_path: Path,
    reference_path: Path,
) -> RaisReconciliationResult:
    if not quality_path.exists():
        raise FileNotFoundError(quality_path)
    if not reference_path.exists():
        raise FileNotFoundError(reference_path)

    quality = _read_json(quality_path)
    references = _read_json(reference_path)
    reference = references.get(str(year))
    if not isinstance(reference, dict):
        raise ValueError(f"Referência oficial RAIS ausente para {year}.")

    if int(quality.get("year") or 0) != year:
        raise ValueError("Ano do relatório de qualidade RAIS diverge do solicitado.")

    expected = int(reference.get("active_links") or 0)
    observed = int(quality.get("rows_active_source") or 0)
    if expected <= 0:
        raise ValueError("Referência oficial RAIS possui total ativo inválido.")

    source_partition_complete = quality.get("source_partition_complete") is True
    unknown_status = int(quality.get("rows_unknown_status_source") or 0)
    year_mismatch = int(quality.get("rows_year_mismatch_source") or 0)
    tech_rows = int(quality.get("rows_tech") or 0)
    difference = observed - expected

    reconciled = (
        source_partition_complete
        and unknown_status == 0
        and year_mismatch == 0
        and observed == expected
        and 0 <= tech_rows <= observed
    )

    return RaisReconciliationResult(
        year=year,
        expected_active=expected,
        observed_active=observed,
        difference=difference,
        source_partition_complete=source_partition_complete,
        unknown_status_rows=unknown_status,
        year_mismatch_rows=year_mismatch,
        tech_rows=tech_rows,
        reconciled=reconciled,
        gold_ready=reconciled,
        publication_ready=False,
        source=str(reference.get("source") or ""),
        source_url=str(reference.get("source_url") or ""),
    )


def write_rais_reconciliation(
    result: RaisReconciliationResult,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
