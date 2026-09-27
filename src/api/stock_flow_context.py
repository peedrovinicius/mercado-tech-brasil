from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.api.occupation_analysis import build_occupation_family_trend
from src.api.publication import (
    latest_published_rais_year,
    published_competencies,
    published_rais_json_path,
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Artefato inválido: {path}")
    return payload


def build_stock_flow_context(
    *,
    gold_dir: Path,
    cbo_config_path: Path,
) -> dict[str, object]:
    rais_year = latest_published_rais_year(gold_dir)
    if rais_year is None:
        raise ValueError("Nenhuma RAIS anual publicada disponível.")

    caged_year = rais_year + 1
    competencies = [
        competence
        for competence in published_competencies(gold_dir)
        if competence.startswith(str(caged_year))
    ]
    if not competencies:
        raise ValueError(
            f"Nenhuma competência Novo CAGED publicada para {caged_year}."
        )

    rais_path = published_rais_json_path(
        gold_dir,
        prefix="rais-by-cbo-family",
        year=rais_year,
    )
    if rais_path is None:
        raise FileNotFoundError(
            f"Gold RAIS por família não encontrado para {rais_year}."
        )

    rais_payload = _read_json(rais_path)
    raw_rais_items = rais_payload.get("items")
    if not isinstance(raw_rais_items, list):
        raise TypeError("RAIS por família sem lista de itens válida.")

    trend = build_occupation_family_trend(
        gold_dir=gold_dir,
        cbo_config_path=cbo_config_path,
        competencies=competencies,
    )
    raw_flow_families = trend.get("families")
    if not isinstance(raw_flow_families, list):
        raise TypeError("Série CAGED por família inválida.")

    rais_by_family: dict[str, dict[str, Any]] = {}
    for raw in raw_rais_items:
        if not isinstance(raw, dict):
            raise TypeError("Item RAIS por família inválido.")
        family = str(raw.get("cbo_familia") or "")
        stock = int(raw.get("active_stock") or 0)
        if not family or stock <= 0:
            raise ValueError(
                f"RAIS por família inválida para {family!r}."
            )
        rais_by_family[family] = raw

    flow_by_family: dict[str, dict[str, Any]] = {}
    for raw in raw_flow_families:
        if not isinstance(raw, dict):
            raise TypeError("Item CAGED por família inválido.")
        family = str(raw.get("cbo_familia") or "")
        flow_by_family[family] = raw

    if set(rais_by_family) != set(flow_by_family):
        raise ValueError(
            "Famílias CBO divergentes entre RAIS e Novo CAGED publicados."
        )

    total_stock = sum(
        int(item["active_stock"]) for item in rais_by_family.values()
    )
    total_admissions = sum(
        int(item.get("admissions") or 0) for item in flow_by_family.values()
    )
    total_dismissals = sum(
        int(item.get("dismissals") or 0) for item in flow_by_family.values()
    )
    total_balance = sum(
        int(item.get("balance") or 0) for item in flow_by_family.values()
    )

    if total_admissions - total_dismissals != total_balance:
        raise ValueError("Fluxo CAGED acumulado possui saldo inconsistente.")

    families: list[dict[str, object]] = []
    for family, rais_item in rais_by_family.items():
        flow_item = flow_by_family[family]
        stock = int(rais_item["active_stock"])
        admissions = int(flow_item.get("admissions") or 0)
        dismissals = int(flow_item.get("dismissals") or 0)
        balance = int(flow_item.get("balance") or 0)
        stock_share = stock / total_stock if total_stock else 0
        admissions_share = (
            admissions / total_admissions if total_admissions else 0
        )

        families.append(
            {
                "cbo_familia": family,
                "cbo_familia_nome": str(
                    rais_item.get("cbo_familia_nome")
                    or flow_item.get("cbo_familia_nome")
                    or family
                ),
                "active_stock": stock,
                "share_of_tech_stock": stock_share,
                "admissions": admissions,
                "dismissals": dismissals,
                "balance": balance,
                "share_of_tech_admissions": admissions_share,
                "admissions_per_100_prior_stock": admissions / stock * 100,
                "dismissals_per_100_prior_stock": dismissals / stock * 100,
                "balance_per_100_prior_stock": balance / stock * 100,
                "composition_gap_pp": (
                    admissions_share - stock_share
                )
                * 100,
            }
        )

    families.sort(
        key=lambda item: int(item["active_stock"]),
        reverse=True,
    )

    return {
        "stock_source": str(
            rais_payload.get("source")
            or "RAIS / Ministério do Trabalho e Emprego"
        ),
        "flow_source": "Novo CAGED / MTE",
        "scope": "mesmo recorte CBO de tecnologia versionado",
        "interpretation": "descriptive_scale_context",
        "rais_year": rais_year,
        "stock_reference_date": str(
            rais_payload.get("reference_date") or f"{rais_year}-12-31"
        ),
        "caged_year": caged_year,
        "caged_from": competencies[0],
        "caged_to": competencies[-1],
        "published_months": len(competencies),
        "totals": {
            "active_stock": total_stock,
            "admissions": total_admissions,
            "dismissals": total_dismissals,
            "balance": total_balance,
            "admissions_per_100_prior_stock": (
                total_admissions / total_stock * 100
            ),
            "dismissals_per_100_prior_stock": (
                total_dismissals / total_stock * 100
            ),
            "balance_per_100_prior_stock": (
                total_balance / total_stock * 100
            ),
        },
        "families": families,
        "methodological_warning": (
            "A RAIS mede estoque de vínculos ativos em 31/12 e o Novo CAGED "
            "mede eventos de admissão e desligamento ao longo do período seguinte. "
            "Os quocientes por 100 vínculos servem apenas como escala descritiva. "
            "Eles não representam turnover, probabilidade individual, crescimento "
            "do estoque nem quantidade de pessoas únicas."
        ),
    }
