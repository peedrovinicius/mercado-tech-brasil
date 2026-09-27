from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.api.publication import published_competencies


@dataclass(frozen=True)
class IncrementalPreparationStatus:
    ready: bool
    reason: str
    latest_published: str | None
    next_expected: str | None
    candidate: str | None
    reference_published_at: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Referências oficiais inválidas: {path}")
    return payload


def _next_month(yearmonth: str) -> str:
    if len(yearmonth) != 6 or not yearmonth.isdigit():
        raise ValueError(f"Competência inválida: {yearmonth}")

    year = int(yearmonth[:4])
    month = int(yearmonth[4:])
    if not 1 <= month <= 12:
        raise ValueError(f"Competência inválida: {yearmonth}")

    if month == 12:
        return f"{year + 1:04d}01"
    return f"{year:04d}{month + 1:02d}"


def _reference_effective_date(reference: dict[str, Any]) -> date:
    raw = reference.get("published_at")
    if not isinstance(raw, str):
        raise TypeError("Referência oficial sem published_at.")

    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"published_at inválido: {raw}") from exc


def _validate_reference(competence: str, reference: object) -> dict[str, Any]:
    if not isinstance(reference, dict):
        raise TypeError(f"Referência oficial inválida para {competence}.")

    if reference.get("reference_kind") != "published_monthly_mov":
        raise ValueError(
            f"Referência {competence} não é uma publicação mensal MOV."
        )

    for field in ("source", "source_url", "published_at"):
        if not str(reference.get(field) or "").strip():
            raise ValueError(
                f"Referência {competence} sem campo obrigatório: {field}."
            )

    admissions = int(reference.get("admissoes") or 0)
    dismissals = int(reference.get("desligamentos") or 0)
    balance = int(reference.get("saldo") or 0)

    if admissions <= 0 or dismissals <= 0:
        raise ValueError(f"Referência {competence} possui totais inválidos.")
    if admissions - dismissals != balance:
        raise ValueError(
            f"Referência {competence} possui saldo aritmeticamente inconsistente."
        )

    _reference_effective_date(reference)
    return reference


def evaluate_next_competence(
    *,
    reference_path: Path,
    gold_path: Path,
    today: date | None = None,
) -> IncrementalPreparationStatus:
    references = _read_json(reference_path)
    effective_today = today or datetime.now(UTC).date()

    validated: dict[str, dict[str, Any]] = {}
    for competence, reference in references.items():
        if len(competence) != 6 or not competence.isdigit():
            raise ValueError(f"Chave de competência inválida: {competence}")
        validated[competence] = _validate_reference(competence, reference)

    published = published_competencies(gold_path)
    latest = published[-1] if published else None

    if latest is None:
        eligible = [
            competence
            for competence, reference in validated.items()
            if _reference_effective_date(reference) <= effective_today
        ]
        if not eligible:
            return IncrementalPreparationStatus(
                ready=False,
                reason="official_reference_not_registered",
                latest_published=None,
                next_expected=None,
                candidate=None,
                reference_published_at=None,
            )

        candidate = min(eligible)
        reference = validated[candidate]
        return IncrementalPreparationStatus(
            ready=True,
            reason="ready",
            latest_published=None,
            next_expected=candidate,
            candidate=candidate,
            reference_published_at=str(reference["published_at"]),
        )

    next_expected = _next_month(latest)
    reference = validated.get(next_expected)

    if reference is None:
        later = sorted(
            competence
            for competence in validated
            if competence > next_expected
        )
        reason = "reference_gap" if later else "official_reference_not_registered"
        return IncrementalPreparationStatus(
            ready=False,
            reason=reason,
            latest_published=latest,
            next_expected=next_expected,
            candidate=None,
            reference_published_at=None,
        )

    published_at = _reference_effective_date(reference)
    if published_at > effective_today:
        return IncrementalPreparationStatus(
            ready=False,
            reason="reference_not_effective_yet",
            latest_published=latest,
            next_expected=next_expected,
            candidate=None,
            reference_published_at=str(reference["published_at"]),
        )

    return IncrementalPreparationStatus(
        ready=True,
        reason="ready",
        latest_published=latest,
        next_expected=next_expected,
        candidate=next_expected,
        reference_published_at=str(reference["published_at"]),
    )


def validate_requested_competence(
    yearmonth: str,
    *,
    reference_path: Path,
    gold_path: Path,
    allow_published: bool = False,
    today: date | None = None,
) -> IncrementalPreparationStatus:
    status = evaluate_next_competence(
        reference_path=reference_path,
        gold_path=gold_path,
        today=today,
    )

    if status.ready and status.candidate == yearmonth:
        return status

    if allow_published and yearmonth in published_competencies(gold_path):
        references = _read_json(reference_path)
        reference = _validate_reference(yearmonth, references.get(yearmonth))
        published_at = _reference_effective_date(reference)
        effective_today = today or datetime.now(UTC).date()
        if published_at > effective_today:
            raise ValueError(
                f"Referência oficial de {yearmonth} ainda não está efetiva."
            )
        return IncrementalPreparationStatus(
            ready=True,
            reason="published_reaudit",
            latest_published=yearmonth,
            next_expected=status.next_expected,
            candidate=yearmonth,
            reference_published_at=str(reference["published_at"]),
        )

    raise ValueError(
        f"Competência {yearmonth} não elegível para auditoria incremental: "
        f"{status.reason}; próxima esperada={status.next_expected or 'nenhuma'}."
    )
