from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.gold.aggregate import enrich_municipality_items


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON inválido: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def enrich_published_municipality_population(
    *,
    yearmonth: str,
    population_year: int,
    gold_dir: Path,
    population_cache_path: Path,
    source_url: str,
    published_at: str,
) -> dict[str, Any]:
    if len(yearmonth) != 6 or not yearmonth.isdigit():
        raise ValueError("Competência deve usar o formato AAAAMM.")

    gate_path = gold_dir / f"publication-gate-{yearmonth}.json"
    if not gate_path.exists():
        raise FileNotFoundError(
            f"Gate publicado ausente para {yearmonth}."
        )
    gate = _read_json(gate_path)
    if gate.get("publishable") is not True:
        raise ValueError(
            f"Competência {yearmonth} não está publicada."
        )

    municipality_path = gold_dir / f"by-municipality-{yearmonth}.json"
    if not municipality_path.exists():
        raise FileNotFoundError(
            f"Gold municipal ausente para {yearmonth}."
        )
    if not population_cache_path.exists():
        raise FileNotFoundError(
            f"Cache populacional ausente: {population_cache_path}"
        )

    population = _read_json(population_cache_path)
    cache_year = int(population.get("reference_year") or 0)
    if cache_year != population_year:
        raise ValueError(
            "Ano do cache populacional diverge do alvo de enriquecimento."
        )

    municipalities = population.get("municipalities")
    if not isinstance(municipalities, dict) or len(municipalities) < 5000:
        raise ValueError("Cache populacional possui cobertura inesperada.")

    payload = _read_json(municipality_path)
    if str(payload.get("competence") or "") != yearmonth:
        raise ValueError("Competência do Gold municipal diverge do alvo.")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("Gold municipal não possui itens para enriquecer.")
    items = [
        dict(item)
        for item in raw_items
        if isinstance(item, dict)
    ]
    if len(items) != len(raw_items):
        raise TypeError("Gold municipal contém item inválido.")

    totals_before = {
        "admissions": sum(int(item.get("admissions") or 0) for item in items),
        "dismissals": sum(
            int(item.get("dismissals") or 0) for item in items
        ),
        "balance": sum(int(item.get("balance") or 0) for item in items),
    }
    original_sha256 = _sha256(municipality_path)

    enriched = enrich_municipality_items(
        items,
        cache_path=None,
        population_cache_path=population_cache_path,
    )

    identified = 0
    residual = 0
    missing: list[str] = []
    for item in enriched:
        code = str(item.get("municipio_codigo_caged") or "")
        if code == "999999":
            residual += 1
            if any(
                item.get(key) is not None
                for key in (
                    "population_estimate",
                    "admissions_per_100k",
                    "dismissals_per_100k",
                    "balance_per_100k",
                )
            ):
                raise ValueError(
                    "Residual municipal recebeu denominador populacional."
                )
            continue

        identified += 1
        ibge_code = str(item.get("municipio_codigo_ibge") or "")
        population_value = item.get("population_estimate")
        if (
            len(ibge_code) != 7
            or not ibge_code.isdigit()
            or population_value is None
            or int(population_value) <= 0
        ):
            missing.append(ibge_code or code)
            continue

        expected = {
            "admissions_per_100k": round(
                int(item.get("admissions") or 0)
                * 100000
                / int(population_value),
                4,
            ),
            "dismissals_per_100k": round(
                int(item.get("dismissals") or 0)
                * 100000
                / int(population_value),
                4,
            ),
            "balance_per_100k": round(
                int(item.get("balance") or 0)
                * 100000
                / int(population_value),
                4,
            ),
        }
        for key, expected_value in expected.items():
            if item.get(key) != expected_value:
                raise ValueError(
                    f"Taxa municipal inconsistente: {ibge_code} {key}."
                )

    if missing:
        sample = ", ".join(sorted(set(missing))[:10])
        raise ValueError(
            "Cobertura populacional incompleta para municípios identificados: "
            f"{len(missing)} ausentes. Amostra: {sample}"
        )

    totals_after = {
        "admissions": sum(
            int(item.get("admissions") or 0) for item in enriched
        ),
        "dismissals": sum(
            int(item.get("dismissals") or 0) for item in enriched
        ),
        "balance": sum(
            int(item.get("balance") or 0) for item in enriched
        ),
    }
    if totals_before != totals_after:
        raise ValueError(
            "Enriquecimento populacional alterou os totais de movimentação."
        )

    population_sha256 = _sha256(population_cache_path)
    payload.update(
        {
            "population_source": str(
                population.get("source") or "IBGE SIDRA"
            ),
            "population_reference_year": population_year,
            "population_reference_date": str(
                population.get("reference_date")
                or f"{population_year}-07-01"
            ),
            "population_source_url": source_url,
            "population_published_at": published_at,
            "population_cache_sha256": population_sha256,
            "population_enrichment_status": "complete",
            "items": enriched,
        }
    )
    _write_json(municipality_path, payload)
    enriched_sha256 = _sha256(municipality_path)

    report = {
        "version": 1,
        "competence": yearmonth,
        "population_year": population_year,
        "population_reference_date": payload["population_reference_date"],
        "population_source": payload["population_source"],
        "population_source_url": source_url,
        "population_published_at": published_at,
        "population_cache_sha256": population_sha256,
        "municipality_artifact_before_sha256": original_sha256,
        "municipality_artifact_sha256": enriched_sha256,
        "identified_municipalities": identified,
        "residual_municipalities": residual,
        "matched_population": identified,
        "missing_population": 0,
        "coverage_complete": True,
        "totals_before": totals_before,
        "totals_after": totals_after,
    }
    report_path = gold_dir / f"population-enrichment-{yearmonth}.json"
    _write_json(report_path, report)
    return report
