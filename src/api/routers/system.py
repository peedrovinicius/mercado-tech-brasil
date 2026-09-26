from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.exc import SQLAlchemyError

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

    overview_files = sorted(settings.gold_path.glob("overview-*.json"))
    market_files = sorted(settings.gold_path.glob("market-*.parquet"))
    data_loaded = bool(overview_files and market_files)

    return {
        "api": "ready",
        "data_loaded": data_loaded,
        "backend": "files",
        "latest_overview": overview_files[-1].name if overview_files else None,
        "latest_market": market_files[-1].name if market_files else None,
        "note": (
            "A API está operacional. data_loaded=true somente quando a camada Gold "
            "possui overview e tabela analítica correspondentes."
        ),
    }
