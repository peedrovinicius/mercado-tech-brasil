from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class QualityReport:
    source: str
    competence: str
    rows_read: int
    rows_valid: int
    rows_rejected: int
    rejection_reasons: dict[str, int]
    generated_at_utc: str

    @property
    def valid_rate(self) -> float:
        if self.rows_read == 0:
            return 0.0
        return round(self.rows_valid / self.rows_read, 6)


def make_report(
    *,
    source: str,
    competence: str,
    rows_read: int,
    rows_valid: int,
    rejection_reasons: dict[str, int],
) -> QualityReport:
    rows_rejected = sum(rejection_reasons.values())
    if rows_valid + rows_rejected > rows_read:
        raise ValueError("Relatório inconsistente: válidos + rejeitados > lidos.")

    return QualityReport(
        source=source,
        competence=competence,
        rows_read=rows_read,
        rows_valid=rows_valid,
        rows_rejected=rows_rejected,
        rejection_reasons=rejection_reasons,
        generated_at_utc=datetime.now(UTC).isoformat(),
    )


def write_report(report: QualityReport, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report) | {"valid_rate": report.valid_rate}
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
