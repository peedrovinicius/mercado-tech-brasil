from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from src.api.publication import (
    latest_published_competence,
    published_competencies,
)
from src.core.settings import settings
from src.db.repository import (
    fetch_by_municipality,
    fetch_by_occupation,
    fetch_by_uf,
    fetch_trend,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

NORTHEAST_UFS = frozenset({"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"})


def _published_json(prefix: str) -> Path:
    competence = latest_published_competence(settings.gold_path)
    if competence is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Indicador ainda não disponível. O pipeline oficial precisa ser "
                "processado, validado e aprovado antes da publicação."
            ),
        )

    path = settings.gold_path / f"{prefix}-{competence}.json"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Artefato publicado ausente para {prefix} em {competence}.",
        )
    return path


def _by_uf_payload(limit: int) -> dict[str, object]:
    if settings.data_backend == "postgres":
        try:
            payload = fetch_by_uf(settings.database_url, limit=limit)
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=503,
                detail="PostgreSQL indisponível para leitura por UF.",
            ) from exc
        if payload is None:
            raise HTTPException(
                status_code=503,
                detail="Nenhuma competência aprovada foi carregada no PostgreSQL.",
            )
        return payload

    payload = json.loads(_published_json("by-uf").read_text(encoding="utf-8"))
    return {
        **payload,
        "items": payload.get("items", [])[:limit],
    }


@router.get("/by-uf")
def by_uf(limit: int = Query(default=27, ge=1, le=27)) -> dict[str, object]:
    return _by_uf_payload(limit)


def _territory_item(
    *,
    key: str,
    label: str,
    items: list[dict[str, object]],
    national_admissions: int,
) -> dict[str, object]:
    admissions = sum(int(item.get("admissions") or 0) for item in items)
    dismissals = sum(int(item.get("dismissals") or 0) for item in items)
    balance = sum(int(item.get("balance") or 0) for item in items)

    return {
        "key": key,
        "label": label,
        "admissions": admissions,
        "dismissals": dismissals,
        "balance": balance,
        "share_national_admissions": (
            admissions / national_admissions if national_admissions else 0
        ),
    }


@router.get("/territorial-comparison")
def territorial_comparison() -> dict[str, object]:
    payload = _by_uf_payload(27)
    raw_items = payload.get("items", [])
    items = [
        item
        for item in raw_items
        if isinstance(item, dict)
    ]

    brasil_admissions = sum(int(item.get("admissions") or 0) for item in items)
    nordeste_items = [
        item for item in items if str(item.get("uf") or "") in NORTHEAST_UFS
    ]
    ceara_items = [
        item for item in items if str(item.get("uf") or "") == "CE"
    ]

    comparison = [
        _territory_item(
            key="BR",
            label="Brasil",
            items=items,
            national_admissions=brasil_admissions,
        ),
        _territory_item(
            key="NE",
            label="Nordeste",
            items=nordeste_items,
            national_admissions=brasil_admissions,
        ),
        _territory_item(
            key="CE",
            label="Ceará",
            items=ceara_items,
            national_admissions=brasil_admissions,
        ),
    ]

    nordeste_admissions = int(comparison[1]["admissions"])
    ceara_admissions = int(comparison[2]["admissions"])

    return {
        "competence": payload.get("competence"),
        "source": payload.get("source"),
        "scope": "recorte CBO de tecnologia versionado",
        "items": comparison,
        "ceara_share_northeast_admissions": (
            ceara_admissions / nordeste_admissions
            if nordeste_admissions
            else 0
        ),
    }


@router.get("/by-occupation")
def by_occupation(limit: int = Query(default=10, ge=1, le=50)) -> dict[str, object]:
    if settings.data_backend == "postgres":
        try:
            payload = fetch_by_occupation(settings.database_url, limit=limit)
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=503,
                detail="PostgreSQL indisponível para leitura por ocupação.",
            ) from exc
        if payload is None:
            raise HTTPException(
                status_code=503,
                detail="Nenhuma competência aprovada foi carregada no PostgreSQL.",
            )
        return payload

    payload = json.loads(
        _published_json("by-occupation").read_text(encoding="utf-8")
    )
    return {
        **payload,
        "items": payload.get("items", [])[:limit],
    }


@router.get("/by-municipality")
def by_municipality(
    limit: int = Query(default=20, ge=1, le=200),
) -> dict[str, object]:
    if settings.data_backend == "postgres":
        try:
            payload = fetch_by_municipality(settings.database_url, limit=limit)
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=503,
                detail="PostgreSQL indisponível para leitura por município.",
            ) from exc
        if payload is None:
            raise HTTPException(
                status_code=503,
                detail="Nenhuma competência municipal aprovada foi carregada.",
            )
        return payload

    payload = json.loads(
        _published_json("by-municipality").read_text(encoding="utf-8")
    )
    return {
        **payload,
        "items": payload.get("items", [])[:limit],
    }


def _trend_payload() -> dict[str, object]:
    if settings.data_backend == "postgres":
        try:
            payload = fetch_trend(settings.database_url)
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=503,
                detail="PostgreSQL indisponível para leitura da série histórica.",
            ) from exc
        if payload is None:
            raise HTTPException(
                status_code=503,
                detail="Ainda não há competências aprovadas para série histórica.",
            )
        return payload

    approved = set(published_competencies(settings.gold_path))
    path = settings.gold_path / "trend.json"
    if not approved or not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Série histórica publicada ainda não disponível.",
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    items = [
        item
        for item in payload.get("items", [])
        if isinstance(item, dict)
        and str(item.get("competence") or "") in approved
    ]
    if not items:
        raise HTTPException(
            status_code=503,
            detail="Série histórica não possui competências aprovadas.",
        )
    return {**payload, "items": items}


@router.get("/trend")
def trend() -> dict[str, object]:
    return _trend_payload()


@router.get("/temporal-summary")
def temporal_summary() -> dict[str, object]:
    payload = _trend_payload()
    raw_items = payload.get("items", [])
    items = [
        item
        for item in raw_items
        if isinstance(item, dict)
        and len(str(item.get("competence") or "")) == 6
    ]

    periods: dict[str, dict[str, object]] = {}
    for item in sorted(items, key=lambda value: str(value["competence"])):
        competence = str(item["competence"])
        year = int(competence[:4])
        month = int(competence[4:6])
        quarter = ((month - 1) // 3) + 1
        key = f"{year}Q{quarter}"

        bucket = periods.setdefault(
            key,
            {
                "key": key,
                "label": f"{quarter}º trimestre de {year}",
                "year": year,
                "quarter": quarter,
                "competencies": [],
                "admissions": 0,
                "dismissals": 0,
                "balance": 0,
            },
        )
        competencies = bucket["competencies"]
        if isinstance(competencies, list):
            competencies.append(competence)
        bucket["admissions"] = int(bucket["admissions"]) + int(
            item.get("admissions") or 0
        )
        bucket["dismissals"] = int(bucket["dismissals"]) + int(
            item.get("dismissals") or 0
        )
        bucket["balance"] = int(bucket["balance"]) + int(item.get("balance") or 0)

    period_items: list[dict[str, object]] = []
    for bucket in periods.values():
        competencies = bucket["competencies"]
        if not isinstance(competencies, list) or not competencies:
            continue
        published_months = len(competencies)
        balance = int(bucket["balance"])
        period_items.append(
            {
                **bucket,
                "start_competence": competencies[0],
                "end_competence": competencies[-1],
                "published_months": published_months,
                "complete": published_months == 3,
                "average_monthly_balance": round(balance / published_months, 2),
            }
        )

    admissions = sum(int(item.get("admissions") or 0) for item in items)
    dismissals = sum(int(item.get("dismissals") or 0) for item in items)
    balance = sum(int(item.get("balance") or 0) for item in items)
    competencies = [str(item["competence"]) for item in items]

    return {
        "source": payload.get("source"),
        "scope": payload.get("scope"),
        "published_from": competencies[0],
        "published_to": competencies[-1],
        "published_months": len(competencies),
        "cumulative": {
            "admissions": admissions,
            "dismissals": dismissals,
            "balance": balance,
        },
        "periods": period_items,
    }
