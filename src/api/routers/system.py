from __future__ import annotations

from fastapi import APIRouter

from src.core.settings import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "project": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
    }


@router.get("/readiness")
def readiness() -> dict[str, object]:
    overview_files = sorted(settings.gold_path.glob("overview-*.json"))
    market_files = sorted(settings.gold_path.glob("market-*.parquet"))
    data_loaded = bool(overview_files and market_files)

    return {
        "api": "ready",
        "data_loaded": data_loaded,
        "latest_overview": overview_files[-1].name if overview_files else None,
        "latest_market": market_files[-1].name if market_files else None,
        "note": (
            "A API está operacional. data_loaded=true somente quando a camada Gold "
            "possui overview e tabela analítica correspondentes."
        ),
    }
