from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Artefato inválido: {path}")
    return payload


def _family_names(cbo_config_path: Path) -> dict[str, str]:
    payload = yaml.safe_load(cbo_config_path.read_text(encoding="utf-8"))
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, dict) or not families:
        raise TypeError("Configuração CBO sem famílias válidas.")
    return {str(code): str(name) for code, name in families.items()}


def build_occupation_family_trend(
    *,
    gold_dir: Path,
    cbo_config_path: Path,
    competencies: list[str],
) -> dict[str, object]:
    if not competencies:
        raise ValueError("Nenhuma competência publicada disponível.")

    ordered_competencies = sorted(set(competencies))
    family_names = _family_names(cbo_config_path)
    monthly_by_family: dict[str, list[dict[str, object]]] = {
        family: [] for family in family_names
    }
    cumulative: dict[str, dict[str, int]] = {
        family: {
            "admissions": 0,
            "dismissals": 0,
            "balance": 0,
        }
        for family in family_names
    }

    for competence in ordered_competencies:
        path = gold_dir / f"by-occupation-{competence}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Artefato ocupacional publicado ausente: {path}"
            )

        payload = _read_json(path)
        if str(payload.get("competence") or "") != competence:
            raise ValueError(
                f"Competência divergente em {path.name}."
            )

        per_family: dict[str, dict[str, int]] = {
            family: {
                "admissions": 0,
                "dismissals": 0,
                "balance": 0,
            }
            for family in family_names
        }

        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raise TypeError(f"Lista de ocupações inválida em {path.name}.")

        for raw in raw_items:
            if not isinstance(raw, dict):
                raise TypeError(f"Item ocupacional inválido em {path.name}.")

            family = str(raw.get("cbo_familia") or "")
            if family not in family_names:
                raise ValueError(
                    f"Família CBO fora do recorte versionado: {family!r}."
                )

            admissions = int(raw.get("admissions") or 0)
            dismissals = int(raw.get("dismissals") or 0)
            balance = int(raw.get("balance") or 0)
            if admissions < 0 or dismissals < 0:
                raise ValueError(
                    f"Contagem negativa em {path.name} para {family}."
                )
            if admissions - dismissals != balance:
                raise ValueError(
                    f"Saldo inconsistente em {path.name} para {family}."
                )

            bucket = per_family[family]
            bucket["admissions"] += admissions
            bucket["dismissals"] += dismissals
            bucket["balance"] += balance

        for family in family_names:
            metrics = per_family[family]
            monthly_by_family[family].append(
                {
                    "competence": competence,
                    **metrics,
                }
            )
            cumulative[family]["admissions"] += metrics["admissions"]
            cumulative[family]["dismissals"] += metrics["dismissals"]
            cumulative[family]["balance"] += metrics["balance"]

    total_admissions = sum(
        metrics["admissions"] for metrics in cumulative.values()
    )
    families = []
    for family, name in family_names.items():
        metrics = cumulative[family]
        families.append(
            {
                "cbo_familia": family,
                "cbo_familia_nome": name,
                "admissions": metrics["admissions"],
                "dismissals": metrics["dismissals"],
                "balance": metrics["balance"],
                "share_of_tech_admissions": (
                    metrics["admissions"] / total_admissions
                    if total_admissions
                    else 0
                ),
                "monthly": monthly_by_family[family],
            }
        )

    families.sort(
        key=lambda item: int(item["admissions"]),
        reverse=True,
    )

    return {
        "source": "Novo CAGED / MTE",
        "scope": "recorte CBO de tecnologia versionado",
        "dimension": "familia_cbo",
        "published_from": ordered_competencies[0],
        "published_to": ordered_competencies[-1],
        "published_months": len(ordered_competencies),
        "families": families,
    }
