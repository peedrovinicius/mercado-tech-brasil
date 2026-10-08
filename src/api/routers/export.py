from __future__ import annotations

import csv
import io
import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from src.api.publication import latest_published_competence
from src.core.settings import settings

router = APIRouter(prefix="/export", tags=["export"])

DatasetName = Literal["by-uf", "by-occupation", "by-municipality"]


def _csv_bytes(items: list[dict[str, object]]) -> bytes:
    if not items:
        return b""

    fieldnames: list[str] = []
    seen: set[str] = set()
    for item in items:
        for key in item:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    # Preserve numeric values while preventing spreadsheet formula execution
    # from untrusted text cells in downloaded CSV files.
    def safe_cell(value: object) -> object:
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows({key: safe_cell(value) for key, value in item.items()} for item in items)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


@router.get("/latest/{dataset}.csv")
def export_latest(dataset: DatasetName) -> Response:
    competence = latest_published_competence(settings.gold_path)
    if competence is None:
        raise HTTPException(
            status_code=503,
            detail="Nenhuma competência publicada disponível para exportação.",
        )

    path = settings.gold_path / f"{dataset}-{competence}.json"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset publicado não encontrado: {dataset}.",
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        raise HTTPException(
            status_code=500,
            detail=f"Dataset sem lista de itens válida: {dataset}.",
        )

    rows = [item for item in items if isinstance(item, dict)]
    if len(rows) != len(items):
        raise HTTPException(
            status_code=500,
            detail=f"Dataset contém item inválido: {dataset}.",
        )

    body = _csv_bytes(rows)
    filename = f"mercado-tech-brasil-{dataset}-{competence}.csv"
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Data-Competence": competence,
        },
    )
