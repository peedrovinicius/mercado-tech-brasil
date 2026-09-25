from __future__ import annotations

import json

from fastapi import APIRouter

from src.core.settings import settings

router = APIRouter(prefix="/quality", tags=["data-quality"])


@router.get("/latest")
def latest_quality_report() -> dict[str, object]:
    reports = sorted(settings.gold_path.glob("quality-*.json"))
    if not reports:
        return {
            "status": "not_available",
            "message": "Ainda não existe relatório de qualidade publicado.",
        }

    latest = reports[-1]
    return json.loads(latest.read_text(encoding="utf-8"))
