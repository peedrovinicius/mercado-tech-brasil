from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_cbo_families(path: Path) -> dict[str, str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, dict) or not families:
        raise ValueError("Configuração CBO tech inválida.")
    return {str(code): str(label) for code, label in families.items()}


def build_rais_gold(
    *,
    year: int,
    silver_path: Path,
    reconciliation_path: Path,
    cbo_config_path: Path,
    gold_dir: Path,
) -> dict[str, Path]:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError(
            "Polars não está instalado. Execute pip install -e ."
        ) from exc

    if not silver_path.exists():
        raise FileNotFoundError(silver_path)
    if not reconciliation_path.exists():
        raise FileNotFoundError(reconciliation_path)

    reconciliation = _read_json(reconciliation_path)
    if int(reconciliation.get("year") or 0) != year:
        raise ValueError("Ano da reconciliação RAIS diverge do solicitado.")
    if reconciliation.get("reconciled") is not True:
        raise ValueError("RAIS não está reconciliada com a referência oficial.")
    if reconciliation.get("gold_ready") is not True:
        raise ValueError("Reconciliação RAIS ainda não liberou Gold.")

    expected_active = int(reconciliation.get("expected_active") or 0)
    if expected_active <= 0:
        raise ValueError("Reconciliação RAIS sem total oficial válido.")

    families = _load_cbo_families(cbo_config_path)
    data = pl.read_parquet(silver_path)

    required_columns = {
        "year",
        "cbo_codigo",
        "cbo_familia",
        "uf",
        "active_3112",
    }
    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(
            "Silver RAIS sem colunas obrigatórias para Gold: "
            + ", ".join(sorted(missing))
        )

    if data.filter(pl.col("year") != year).height:
        raise ValueError("Silver RAIS contém ano diferente do solicitado.")
    if data.filter(pl.col("active_3112") != True).height:
        raise ValueError("Silver RAIS contém vínculo não ativo em 31/12.")

    unknown_families = sorted(
        set(data.get_column("cbo_familia").unique().to_list()) - set(families)
    )
    if unknown_families:
        raise ValueError(
            "Silver RAIS contém família fora do recorte tech: "
            + ", ".join(str(value) for value in unknown_families)
        )

    tech_stock = data.height
    if tech_stock > expected_active:
        raise ValueError(
            "Estoque tech não pode exceder o estoque nacional ativo reconciliado."
        )

    gold_dir.mkdir(parents=True, exist_ok=True)

    market_path = gold_dir / f"rais-market-{year}.parquet"
    overview_path = gold_dir / f"rais-overview-{year}.json"
    by_uf_path = gold_dir / f"rais-by-uf-{year}.json"
    by_family_path = gold_dir / f"rais-by-cbo-family-{year}.json"

    market = (
        data.group_by(["uf", "cbo_familia", "cbo_codigo"])
        .agg(pl.len().alias("active_stock"))
        .with_columns(pl.lit(year).alias("year"))
        .select(
            [
                "year",
                "uf",
                "cbo_familia",
                "cbo_codigo",
                "active_stock",
            ]
        )
        .sort(
            ["active_stock", "uf", "cbo_familia", "cbo_codigo"],
            descending=[True, False, False, False],
        )
    )
    market.write_parquet(market_path, compression="zstd")

    by_uf = (
        data.group_by("uf")
        .agg(pl.len().alias("active_stock"))
        .sort(["active_stock", "uf"], descending=[True, False])
        .to_dicts()
    )
    for item in by_uf:
        item["share_of_tech_stock"] = (
            round(int(item["active_stock"]) / tech_stock, 8)
            if tech_stock
            else 0.0
        )

    by_family = (
        data.group_by("cbo_familia")
        .agg(pl.len().alias("active_stock"))
        .sort(["active_stock", "cbo_familia"], descending=[True, False])
        .to_dicts()
    )
    for item in by_family:
        family = str(item["cbo_familia"])
        item["cbo_familia_nome"] = families[family]
        item["share_of_tech_stock"] = (
            round(int(item["active_stock"]) / tech_stock, 8)
            if tech_stock
            else 0.0
        )

    overview = {
        "year": year,
        "reference_date": f"{year}-12-31",
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "scope": "estoque anual de vínculos tech ativos em 31/12",
        "active_stock_tech": tech_stock,
        "active_stock_national_reference": expected_active,
        "share_tech_of_national_active": (
            round(tech_stock / expected_active, 8)
            if expected_active
            else None
        ),
        "cbo_scope_version": 2,
        "cbo_families": sorted(families),
        "uf_count": len(by_uf),
        "market_rows": market.height,
        "reconciliation": {
            "reconciled": True,
            "difference": int(reconciliation.get("difference") or 0),
            "source": reconciliation.get("source"),
            "source_url": reconciliation.get("source_url"),
        },
        "status": "generated_not_published",
        "publication_ready": False,
    }

    _write_json(overview_path, overview)
    _write_json(
        by_uf_path,
        {
            "year": year,
            "reference_date": f"{year}-12-31",
            "source": "RAIS / Ministério do Trabalho e Emprego",
            "scope": "estoque tech ativo por UF",
            "items": by_uf,
            "publication_ready": False,
        },
    )
    _write_json(
        by_family_path,
        {
            "year": year,
            "reference_date": f"{year}-12-31",
            "source": "RAIS / Ministério do Trabalho e Emprego",
            "scope": "estoque tech ativo por família CBO",
            "items": by_family,
            "publication_ready": False,
        },
    )

    return {
        "market": market_path,
        "overview": overview_path,
        "by_uf": by_uf_path,
        "by_cbo_family": by_family_path,
    }
