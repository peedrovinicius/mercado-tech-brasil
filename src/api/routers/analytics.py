from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError

from src.core.settings import settings
from src.db.repository import (
    fetch_by_municipality,
    fetch_by_occupation,
    fetch_by_uf,
    fetch_trend,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _latest_json(prefix: str) -> Path:
    files = sorted(settings.gold_path.glob(f"{prefix}-*.json"))
    if not files:
        raise HTTPException(
            status_code=503,
            detail=(
                "Indicador ainda não disponível. O pipeline oficial precisa ser "
                "processado e validado antes da publicação."
            ),
        )
    return files[-1]


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

    payload = json.loads(_latest_json("by-uf").read_text(encoding="utf-8"))
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

    payload = json.loads(_latest_json("by-occupation").read_text(encoding="utf-8"))
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
        _latest_json("by-municipality").read_text(encoding="utf-8")
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

    path = settings.gold_path / "trend.json"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Série histórica ainda não disponível.",
        )
    return json.loads(path.read_text(encoding="utf-8"))
