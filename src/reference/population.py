from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

SIDRA_TABLE = "6579"
SIDRA_VARIABLE = "9324"
SIDRA_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"


def build_population_url(year: int) -> str:
    if year < 2000 or year > 2100:
        raise ValueError("Ano de referência populacional inválido.")
    return (
        f"{SIDRA_BASE}/{SIDRA_TABLE}/periodos/{year}/variaveis/"
        f"{SIDRA_VARIABLE}?localidades=N6[all]"
    )


def _normalize_population_value(value: object) -> int | None:
    raw = str(value or "").strip()
    if raw in {"", "-", "..", "...", "x", "X"}:
        return None
    digits = raw.replace(".", "").replace(" ", "")
    if not digits.isdigit():
        return None
    population = int(digits)
    return population if population > 0 else None


def parse_population_payload(
    payload: object,
    *,
    year: int,
) -> dict[str, int]:
    if not isinstance(payload, list):
        raise TypeError("Resposta SIDRA de população deve ser uma lista.")

    result: dict[str, int] = {}
    year_key = str(year)

    for variable in payload:
        if not isinstance(variable, dict):
            continue
        for group in variable.get("resultados", []):
            if not isinstance(group, dict):
                continue
            for series in group.get("series", []):
                if not isinstance(series, dict):
                    continue
                locality = series.get("localidade") or {}
                values = series.get("serie") or {}
                if not isinstance(locality, dict) or not isinstance(values, dict):
                    continue

                ibge_code = str(locality.get("id") or "")
                population = _normalize_population_value(values.get(year_key))
                if (
                    len(ibge_code) == 7
                    and ibge_code.isdigit()
                    and population is not None
                ):
                    result[ibge_code] = population

    return result


def fetch_population_estimates(
    year: int,
    *,
    timeout: int = 60,
) -> dict[str, int]:
    url = build_population_url(year)
    request = Request(
        url,
        headers={
            "User-Agent": "mercado-tech-brasil/0.22",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return parse_population_payload(payload, year=year)


def save_population_cache(
    populations: dict[str, int],
    *,
    year: int,
    destination: Path,
) -> None:
    if len(populations) < 5000:
        raise ValueError(
            "Quantidade de municípios abaixo do esperado para a referência populacional."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "source": "IBGE SIDRA",
                "table": SIDRA_TABLE,
                "variable": SIDRA_VARIABLE,
                "reference_year": year,
                "reference_date": f"{year}-07-01",
                "unit": "pessoas",
                "municipalities": dict(sorted(populations.items())),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_population_cache(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    populations = payload.get("municipalities")
    if not isinstance(populations, dict):
        raise TypeError("Cache populacional inválido.")
    return payload
