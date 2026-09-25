from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from src.core.settings import settings

router = APIRouter(prefix="/provenance", tags=["provenance"])


@router.get("/latest")
def latest_provenance() -> dict[str, object]:
    manifests = sorted(
        settings.bronze_path.rglob("*.manifest.json"),
        key=lambda path: path.stat().st_mtime,
    )
    if not manifests:
        raise HTTPException(
            status_code=404,
            detail="Nenhum arquivo oficial foi ingerido ainda.",
        )

    latest = manifests[-1]
    payload = json.loads(latest.read_text(encoding="utf-8"))
    return {
        "source": payload.get("source"),
        "competence": payload.get("competence"),
        "original_name": payload.get("original_name"),
        "size_bytes": payload.get("size_bytes"),
        "sha256": payload.get("sha256"),
        "ingested_at_utc": payload.get("ingested_at_utc"),
        "manifest_path": str(latest.relative_to(settings.root))
        if hasattr(settings, "root")
        else str(latest),
    }
