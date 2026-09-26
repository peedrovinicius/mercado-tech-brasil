from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.exc import SQLAlchemyError

from src.api.publication import latest_published_competence
from src.core.settings import settings
from src.db.repository import fetch_overview

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "project": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "data_backend": getattr(settings, "data_backend", "files"),
    }


@router.get("/readiness")
def readiness() -> dict[str, object]:
    backend = getattr(settings, "data_backend", "files")

    if backend == "postgres":
        try:
            payload = fetch_overview(settings.database_url)
        except SQLAlchemyError:
            return {
                "api": "ready",
                "data_loaded": False,
                "backend": "postgres",
                "note": "API operacional, mas PostgreSQL está indisponível.",
            }
        return {
            "api": "ready",
            "data_loaded": payload is not None,
            "backend": "postgres",
            "note": (
                "data_loaded=true somente quando existe competência aprovada "
                "na camada de serving PostgreSQL."
            ),
        }

    competence = latest_published_competence(settings.gold_path)
    overview_path = (
        settings.gold_path / f"overview-{competence}.json"
        if competence
        else None
    )
    market_path = (
        settings.gold_path / f"market-{competence}.parquet"
        if competence
        else None
    )
    data_loaded = bool(
        competence
        and overview_path
        and overview_path.exists()
        and market_path
        and market_path.exists()
    )

    return {
        "api": "ready",
        "data_loaded": data_loaded,
        "backend": "files",
        "published_competence": competence if data_loaded else None,
        "latest_overview": overview_path.name if data_loaded else None,
        "latest_market": market_path.name if data_loaded else None,
        "note": (
            "A API está operacional. data_loaded=true somente quando a competência "
            "possui gate de publicação aprovado e os artefatos Gold correspondentes."
        ),
    }
