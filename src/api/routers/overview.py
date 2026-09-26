from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

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

    files = sorted(settings.gold_path.glob("overview-*.json"))
    if not files:
        raise HTTPException(
            status_code=503,
            detail=(
                "Indicadores ainda não disponíveis. "
                "O projeto não publica números antes da ingestão e validação dos dados oficiais."
            ),
        )

    return json.loads(files[-1].read_text(encoding="utf-8"))
