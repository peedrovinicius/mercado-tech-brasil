from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.api.publication import (
    latest_published_rais_year,
    published_rais_json_path,
    published_rais_years,
    rais_publication_registry,
)
from src.core.settings import settings

router = APIRouter(prefix="/rais", tags=["rais"])


def _resolve_year(year: int | None) -> int:
    published = published_rais_years(settings.gold_path)

    if year is None:
        latest = latest_published_rais_year(settings.gold_path)
        if latest is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "RAIS anual ainda não publicada. A release precisa passar "
                    "pelo gate automático e pela revisão metodológica."
                ),
            )
        return latest

    if year not in published:
        raise HTTPException(
            status_code=404,
            detail=f"RAIS {year} ainda não está publicada.",
        )
    return year


def _read_published_json(prefix: str, year: int) -> dict[str, object]:
    path = published_rais_json_path(
        settings.gold_path,
        prefix=prefix,
        year=year,
    )
    if path is None or not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Artefato RAIS publicado ausente: {prefix}-{year}.json.",
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Artefato RAIS inválido: {path.name}.",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=503,
            detail=f"Contrato RAIS inválido: {path.name}.",
        )
    return payload


@router.get("/releases")
def releases() -> dict[str, object]:
    published = published_rais_years(settings.gold_path)
    return {
        "latest_published_year": (
            latest_published_rais_year(settings.gold_path)
        ),
        "published_years": published,
        "items": rais_publication_registry(settings.gold_path),
    }


@router.get("/overview")
def overview(
    year: int | None = Query(default=None, ge=1985, le=2100),
) -> dict[str, object]:
    resolved = _resolve_year(year)
    return _read_published_json("rais-overview", resolved)


@router.get("/by-uf")
def by_uf(
    year: int | None = Query(default=None, ge=1985, le=2100),
    limit: int = Query(default=28, ge=1, le=28),
) -> dict[str, object]:
    resolved = _resolve_year(year)
    payload = _read_published_json("rais-by-uf", resolved)
    items = [
        item
        for item in payload.get("items", [])
        if isinstance(item, dict)
    ]
    return {
        **payload,
        "items": items[:limit],
    }


@router.get("/by-cbo-family")
def by_cbo_family(
    year: int | None = Query(default=None, ge=1985, le=2100),
    limit: int = Query(default=5, ge=1, le=50),
) -> dict[str, object]:
    resolved = _resolve_year(year)
    payload = _read_published_json("rais-by-cbo-family", resolved)
    items = [
        item
        for item in payload.get("items", [])
        if isinstance(item, dict)
    ]
    return {
        **payload,
        "items": items[:limit],
    }
