from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.core.settings import settings

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
    payload = json.loads(_latest_json("by-uf").read_text(encoding="utf-8"))
    return {
        **payload,
        "items": payload.get("items", [])[:limit],
    }


@router.get("/by-occupation")
def by_occupation(limit: int = Query(default=10, ge=1, le=50)) -> dict[str, object]:
    payload = json.loads(_latest_json("by-occupation").read_text(encoding="utf-8"))
    return {
        **payload,
        "items": payload.get("items", [])[:limit],
    }
