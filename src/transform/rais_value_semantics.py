from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

import yaml


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def load_value_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Contrato de valores RAIS inválido.")

    active = payload.get("active_3112")
    if not isinstance(active, dict):
        raise TypeError("Contrato RAIS não define active_3112.")
    if not active.get("active_values") or not active.get("inactive_values"):
        raise ValueError(
            "Contrato RAIS precisa definir valores ativos e inativos."
        )

    abandoned = payload.get("abandoned_link")
    if not isinstance(abandoned, dict):
        raise TypeError("Contrato RAIS não define abandoned_link.")
    if not abandoned.get("eligible_values") or not abandoned.get("excluded_values"):
        raise ValueError(
            "Contrato RAIS precisa definir valores elegíveis e excluídos "
            "para vínculo abandonado."
        )
    return payload


def normalize_value(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip())
    text = "".join(
        char for char in text if not unicodedata.combining(char)
    )
    return " ".join(text.casefold().split())


def _observed_values(profile: dict[str, Any], concept: str) -> list[str]:
    aggregate = profile.get("aggregate")
    if not isinstance(aggregate, dict):
        raise TypeError("Perfil RAIS não possui bloco aggregate.")

    item = aggregate.get(concept)
    if not isinstance(item, dict):
        raise TypeError(f"Perfil RAIS não possui conceito {concept}.")

    observed = item.get("observed_values")
    if observed is None:
        raise ValueError(
            f"Perfil de {concept} possui muitos valores distintos para "
            "validação exata."
        )
    if not isinstance(observed, list):
        raise TypeError(f"observed_values inválido para {concept}.")
    return [str(value) for value in observed]


def _binary_semantics(
    *,
    profile: dict[str, Any],
    concept: str,
    positive_values: set[str],
    negative_values: set[str],
    reject_unknown: bool,
    reject_blank: bool,
) -> dict[str, object]:
    concept_profile = profile.get("aggregate", {}).get(concept, {})
    blanks = int(concept_profile.get("blank") or 0)
    raw_values = _observed_values(profile, concept)
    normalized_values = {
        normalize_value(value)
        for value in raw_values
        if str(value).strip()
    }
    allowed_values = positive_values | negative_values
    unknown_values = sorted(normalized_values - allowed_values)

    positive_observed = sorted(normalized_values & positive_values)
    negative_observed = sorted(normalized_values & negative_values)

    positive_valid = bool(positive_observed)
    negative_valid = bool(negative_observed)
    unknown_valid = not unknown_values if reject_unknown else True
    blanks_valid = blanks == 0 if reject_blank else True
    valid = (
        positive_valid
        and negative_valid
        and unknown_valid
        and blanks_valid
    )

    return {
        "observed_values_normalized": sorted(normalized_values),
        "positive_observed": positive_observed,
        "negative_observed": negative_observed,
        "unknown_values": unknown_values,
        "blank_values": blanks,
        "valid": valid,
    }


def validate_value_semantics(
    profile_path: Path,
    contract_path: Path,
    destination: Path,
    *,
    year: int,
) -> dict[str, object]:
    profile = _load_json(profile_path)
    contract = load_value_contract(contract_path)

    if profile.get("profile_complete") is not True:
        raise ValueError("Perfil RAIS não está completo.")
    if int(profile.get("year") or 0) != year:
        raise ValueError(
            f"Ano do perfil RAIS difere do solicitado: {profile.get('year')}."
        )

    active_spec = contract["active_3112"]
    active_values = {
        normalize_value(value)
        for value in active_spec.get("active_values", [])
    }
    inactive_values = {
        normalize_value(value)
        for value in active_spec.get("inactive_values", [])
    }
    active_result = _binary_semantics(
        profile=profile,
        concept="active_3112",
        positive_values=active_values,
        negative_values=inactive_values,
        reject_unknown=active_spec.get("reject_unknown_values", True),
        reject_blank=active_spec.get("reject_blank_values", True),
    )

    abandoned_spec = contract["abandoned_link"]
    eligible_values = {
        normalize_value(value)
        for value in abandoned_spec.get("eligible_values", [])
    }
    excluded_values = {
        normalize_value(value)
        for value in abandoned_spec.get("excluded_values", [])
    }
    abandoned_result = _binary_semantics(
        profile=profile,
        concept="abandoned_link",
        positive_values=eligible_values,
        negative_values=excluded_values,
        reject_unknown=abandoned_spec.get("reject_unknown_values", True),
        reject_blank=abandoned_spec.get("reject_blank_values", True),
    )

    year_profile = profile.get("aggregate", {}).get("year", {})
    observed_years = {
        normalize_value(value)
        for value in year_profile.get("observed_values") or []
    }
    year_valid = observed_years == {str(year)}

    valid = (
        bool(active_result["valid"])
        and bool(abandoned_result["valid"])
        and year_valid
    )

    payload: dict[str, object] = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": year,
        "contract_version": contract.get("version"),
        "value_semantics_valid": valid,
        "silver_transform_ready": valid,
        "publication_ready": False,
        "active_3112": {
            "official_active_values": sorted(active_values),
            "official_inactive_values": sorted(inactive_values),
            "active_observed": active_result["positive_observed"],
            "inactive_observed": active_result["negative_observed"],
            **{
                key: value
                for key, value in active_result.items()
                if key not in {"positive_observed", "negative_observed"}
            },
        },
        "abandoned_link": {
            "official_eligible_values": sorted(eligible_values),
            "official_excluded_values": sorted(excluded_values),
            "eligible_observed": abandoned_result["positive_observed"],
            "excluded_observed": abandoned_result["negative_observed"],
            **{
                key: value
                for key, value in abandoned_result.items()
                if key not in {"positive_observed", "negative_observed"}
            },
        },
        "year_check": {
            "expected": str(year),
            "observed": sorted(observed_years),
            "valid": year_valid,
        },
        "note": (
            "silver_transform_ready valida a situação em 31/12 e a qualificação "
            "de vínculo abandonado. Para 2025, o estoque oficial exige vínculo "
            "ativo e não abandonado. A publicação permanece bloqueada até "
            "qualidade, reconciliação anual e gate específico."
        ),
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
