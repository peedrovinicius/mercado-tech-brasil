from __future__ import annotations

import json

from fastapi import APIRouter
from sqlalchemy.exc import SQLAlchemyError

from src.api.publication import (
    latest_published_competence,
    latest_published_rais_year,
    published_competencies,
)
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


@router.get("/release")
def release_state() -> dict[str, object]:
    competencies = published_competencies(settings.gold_path)
    latest_rais_year = latest_published_rais_year(settings.gold_path)

    policy_mode = "unavailable"
    policy_max_competence: str | None = None
    if settings.monthly_coverage_policy_path.exists():
        payload = json.loads(
            settings.monthly_coverage_policy_path.read_text(encoding="utf-8")
        )
        policy_mode = str(payload.get("mode") or "unavailable")
        raw_max = str(payload.get("max_competence") or "")
        policy_max_competence = raw_max or None

    return {
        "project": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "data_backend": getattr(settings, "data_backend", "files"),
        "monthly": {
            "published_count": len(competencies),
            "first_competence": competencies[0] if competencies else None,
            "latest_competence": competencies[-1] if competencies else None,
            "competencies": competencies,
            "policy_mode": policy_mode,
            "policy_max_competence": policy_max_competence,
        },
        "rais": {
            "latest_published_year": latest_rais_year,
        },
    }
