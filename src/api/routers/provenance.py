from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.publication import (
    latest_published_competence,
    latest_published_rais_year,
)
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
        "transport": payload.get("transport"),
        "source_url": payload.get("source_url"),
        "manifest_path": str(latest.relative_to(settings.root))
        if hasattr(settings, "root")
        else str(latest),
    }



def _artifact_metadata(path: Path) -> dict[str, object]:
    body = path.read_bytes()
    return {
        "path": str(path.relative_to(settings.root)),
        "size_bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


@router.get("/release")
def release_provenance() -> dict[str, object]:
    competence = latest_published_competence(settings.gold_path)
    rais_year = latest_published_rais_year(settings.gold_path)

    if competence is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma competência mensal publicada.",
        )

    monthly_names = [
        f"publication-gate-{competence}.json",
        f"overview-{competence}.json",
        f"by-uf-{competence}.json",
        f"by-occupation-{competence}.json",
        f"by-municipality-{competence}.json",
    ]
    population_name = f"population-enrichment-{competence}.json"
    if (settings.gold_path / population_name).exists():
        monthly_names.append(population_name)

    monthly_artifacts = [
        _artifact_metadata(settings.gold_path / name)
        for name in monthly_names
        if (settings.gold_path / name).exists()
    ]

    rais_artifacts: list[dict[str, object]] = []
    if rais_year is not None:
        rais_names = [
            f"rais-publication-gate-{rais_year}.json",
            f"rais-overview-{rais_year}.json",
            f"rais-by-uf-{rais_year}.json",
            f"rais-by-cbo-family-{rais_year}.json",
            f"rais-by-municipality-{rais_year}.json",
        ]
        rais_artifacts = [
            _artifact_metadata(settings.gold_path / name)
            for name in rais_names
            if (settings.gold_path / name).exists()
        ]

    return {
        "version": settings.version,
        "monthly": {
            "competence": competence,
            "artifacts": monthly_artifacts,
        },
        "rais": {
            "year": rais_year,
            "artifacts": rais_artifacts,
        },
    }
