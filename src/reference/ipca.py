from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

SIDRA_TABLE = "1737"
SIDRA_VARIABLE = "2266"
SIDRA_BASE = "https://apisidra.ibge.gov.br/values"


@dataclass(frozen=True)
class IpcaIndex:
    competence: str
    value: Decimal


def _validate_competence(value: str) -> str:
    if not re.fullmatch(r"\d{6}", value):
        raise ValueError("Competência IPCA deve estar no formato AAAAMM.")
    month = int(value[4:])
    if month not in range(1, 13):
        raise ValueError("Mês inválido na competência IPCA.")
    return value


def build_sidra_url(periods: Iterable[str]) -> str:
    normalized = [_validate_competence(str(period)) for period in periods]
    if not normalized:
        raise ValueError("Informe pelo menos uma competência IPCA.")
    period_expression = ",".join(sorted(set(normalized)))
    encoded_periods = quote(period_expression, safe=",")
    return (
        f"{SIDRA_BASE}/t/{SIDRA_TABLE}/n1/all/v/{SIDRA_VARIABLE}/"
        f"p/{encoded_periods}/d/v{SIDRA_VARIABLE}%2013/h/n"
    )


def _extract_competence(row: dict[str, object]) -> str | None:
    for value in row.values():
        candidate = str(value)
        if re.fullmatch(r"\d{6}", candidate):
            month = int(candidate[4:])
            if month in range(1, 13):
                return candidate
    return None


def fetch_ipca_indices(
    periods: Iterable[str],
    *,
    timeout: int = 30,
) -> dict[str, Decimal]:
    url = build_sidra_url(periods)
    request = Request(
        url,
        headers={"User-Agent": "mercado-tech-brasil/0.13"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result: dict[str, Decimal] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        competence = _extract_competence(row)
        raw_value = row.get("V")
        if competence is None or raw_value in (None, "", "..", "...", "-", "x", "X"):
            continue
        result[competence] = Decimal(str(raw_value).replace(",", "."))

    return result


def correct_to_base(
    nominal_value: float | Decimal,
    *,
    observation_index: float | Decimal,
    base_index: float | Decimal,
) -> Decimal:
    nominal = Decimal(str(nominal_value))
    observation = Decimal(str(observation_index))
    base = Decimal(str(base_index))
    if observation <= 0 or base <= 0:
        raise ValueError("Índices IPCA devem ser positivos.")
    return nominal * base / observation


def save_ipca_cache(
    indices: dict[str, Decimal],
    *,
    base_competence: str,
    destination: Path,
) -> None:
    normalized_base = _validate_competence(base_competence)
    if normalized_base not in indices:
        raise ValueError("A competência base precisa existir no cache IPCA.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "source": "IBGE SIDRA",
                "table": SIDRA_TABLE,
                "variable": SIDRA_VARIABLE,
                "base_competence": normalized_base,
                "indices": {
                    competence: str(value)
                    for competence, value in sorted(indices.items())
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_ipca_cache(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
