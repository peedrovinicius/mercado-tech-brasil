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


@router.get("/by-uf")
def by_uf(limit: int = Query(default=27, ge=1, le=27)) -> dict[str, object]:
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


@router.get("/trend")
def trend() -> dict[str, object]:
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
        if str(item.get("competence") or "") in approved
    ]
    if not items:
        raise HTTPException(
            status_code=503,
            detail="Série histórica não possui competências aprovadas.",
        )
    return {**payload, "items": items}
