from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from src.core.settings import settings

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("/overview")
def overview() -> dict[str, object]:
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
