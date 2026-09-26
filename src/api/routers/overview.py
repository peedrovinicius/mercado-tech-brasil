from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.api.publication import latest_published_competence
from src.core.settings import settings
from src.db.repository import fetch_overview

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("/overview")
def overview() -> dict[str, object]:
    if getattr(settings, "data_backend", "files") == "postgres":
        try:
            payload = fetch_overview(settings.database_url)
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=503,
                detail="PostgreSQL indisponível para leitura dos indicadores.",
            ) from exc
        if payload is None:
            raise HTTPException(
                status_code=503,
                detail="Nenhuma competência aprovada foi carregada no PostgreSQL.",
            )
        return payload

    competence = latest_published_competence(settings.gold_path)
    if competence is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Indicadores ainda não disponíveis. "
                "O projeto não publica números antes da ingestão e validação dos dados oficiais."
            ),
        )

    path = settings.gold_path / f"overview-{competence}.json"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="A competência aprovada não possui overview Gold disponível.",
        )

    return json.loads(path.read_text(encoding="utf-8"))
