from __future__ import annotations

import json
from fastapi import APIRouter

from src.core.settings import settings

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/sources")
def sources() -> dict:
    return json.loads(settings.sources_path.read_text(encoding="utf-8"))


@router.get("/coverage")
def coverage() -> dict[str, object]:
    manifests = sorted(settings.bronze_path.rglob("*.manifest.json"))

    if not manifests:
        return {
            "status": "empty",
            "competencies": [],
            "message": "Nenhuma competência oficial foi ingerida ainda.",
        }

    items = []
    for manifest_path in manifests:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        items.append(
            {
                "source": payload.get("source"),
                "competence": payload.get("competence"),
                "sha256": payload.get("sha256"),
                "size_bytes": payload.get("size_bytes"),
                "ingested_at_utc": payload.get("ingested_at_utc"),
            }
        )

    competencies = sorted(
        {item["competence"] for item in items if item.get("competence")}
    )

    return {
        "status": "loaded",
        "competencies": competencies,
        "files": items,
    }
