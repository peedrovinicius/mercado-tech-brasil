from __future__ import annotations

import json
from pathlib import Path

from src.reference.municipalities import fetch_municipalities

RESIDUAL_CODE = "999999"


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON inválido: {path}")
    return payload


def build_rais_municipality_gold(
    *,
    year: int,
    silver_path: Path,
    validation_path: Path,
    gold_dir: Path,
    municipalities: dict[str, dict[str, str]] | None = None,
) -> Path:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError(
            "Polars não está instalado. Execute pip install -e ."
        ) from exc

    validation = _read_json(validation_path)
    if int(validation.get("year") or 0) != year:
        raise ValueError("Ano da validação municipal RAIS diverge.")
    if validation.get("municipality_ready") is not True:
        raise ValueError(
            "Dimensão municipal RAIS ainda não foi validada contra a DTB."
        )

    data = pl.read_parquet(
        silver_path,
        columns=["municipio_codigo", "uf"],
    )
    stock = data.height
    grouped = (
        data.group_by(["municipio_codigo", "uf"])
        .agg(pl.len().alias("active_stock"))
        .sort(
            ["active_stock", "uf", "municipio_codigo"],
            descending=[True, False, False],
        )
        .to_dicts()
    )

    reference = municipalities or fetch_municipalities()
    items: list[dict[str, object]] = []

    for row in grouped:
        code = str(row["municipio_codigo"])
        uf = str(row["uf"])
        active_stock = int(row["active_stock"])

        if code == RESIDUAL_CODE:
            item = {
                "municipio_codigo_rais": code,
                "municipio_codigo_ibge": None,
                "municipio_nome": "Não identificado",
                "uf": "NI",
                "active_stock": active_stock,
                "share_of_tech_stock": (
                    round(active_stock / stock, 8) if stock else 0.0
                ),
            }
            items.append(item)
            continue

        mapped = reference.get(code)
        if mapped is None:
            raise ValueError(
                f"Município RAIS validado sem cadastro IBGE: {code}"
            )
        mapped_uf = str(mapped.get("uf") or "")
        if mapped_uf != uf:
            raise ValueError(
                f"UF divergente para município {code}: {uf}/{mapped_uf}"
            )

        items.append(
            {
                "municipio_codigo_rais": code,
                "municipio_codigo_ibge": mapped["municipio_codigo_ibge"],
                "municipio_nome": mapped["municipio_nome"],
                "uf": uf,
                "active_stock": active_stock,
                "share_of_tech_stock": (
                    round(active_stock / stock, 8) if stock else 0.0
                ),
            }
        )

    total = sum(int(item["active_stock"]) for item in items)
    if total != stock:
        raise ValueError(
            f"Gold municipal RAIS não fecha o Silver: {total}/{stock}"
        )

    payload = {
        "year": year,
        "reference_date": f"{year}-12-31",
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "municipality_reference": "IBGE, Divisão Territorial Brasileira 2025",
        "scope": "estoque tech ativo por município",
        "code_system": (
            "RAIS 6 dígitos validado contra prefixo do código IBGE "
            "de 7 dígitos"
        ),
        "municipality_count": len(items),
        "active_stock_tech": stock,
        "items": items,
        "publication_ready": False,
    }

    gold_dir.mkdir(parents=True, exist_ok=True)
    destination = gold_dir / f"rais-by-municipality-{year}.json"
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination
