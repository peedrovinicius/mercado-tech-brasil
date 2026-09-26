from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from string import hexdigits
from typing import Any

from sqlalchemy import Engine, create_engine, delete, func, insert, select

from src.db.schema import (
    dataset_release,
    market_municipality,
    market_occupation,
    market_uf,
    metadata,
)
from src.validation.publication_gate import evaluate_publication_gate


class ReleaseNotApprovedError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServingPayload:
    competence: date
    release: dict[str, Any]
    uf_items: tuple[dict[str, Any], ...]
    occupation_items: tuple[dict[str, Any], ...]
    municipality_items: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class LoadResult:
    competence: str
    uf_rows: int
    occupation_rows: int
    municipality_rows: int
    source_sha256: str


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _competence_date(yearmonth: str) -> date:
    if len(yearmonth) != 6 or not yearmonth.isdigit():
        raise ValueError("Competência deve estar no formato AAAAMM.")
    year = int(yearmonth[:4])
    month = int(yearmonth[4:])
    if month not in range(1, 13):
        raise ValueError("Mês inválido na competência.")
    return date(year, month, 1)


def _validate_metric_item(
    item: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    admissions = int(item["admissions"])
    dismissals = int(item["dismissals"])
    balance = int(item["balance"])
    if admissions < 0 or dismissals < 0:
        raise ValueError(f"{label}: admissões/desligamentos não podem ser negativos.")
    if admissions - dismissals != balance:
        raise ValueError(f"{label}: saldo inconsistente.")
    return {
        **item,
        "admissions": admissions,
        "dismissals": dismissals,
        "balance": balance,
    }


def build_serving_payload(
    *,
    yearmonth: str,
    gold_dir: Path,
    source_sha256: str,
) -> ServingPayload:
    if len(source_sha256) != 64 or any(char not in hexdigits for char in source_sha256):
        raise ValueError("source_sha256 deve conter 64 caracteres hexadecimais.")

    competence = _competence_date(yearmonth)
    overview = _read_json(gold_dir / f"overview-{yearmonth}.json")
    quality = _read_json(gold_dir / f"quality-{yearmonth}.json")
    by_uf = _read_json(gold_dir / f"by-uf-{yearmonth}.json")
    by_occupation = _read_json(gold_dir / f"by-occupation-{yearmonth}.json")
    by_municipality = _read_json_optional(
        gold_dir / f"by-municipality-{yearmonth}.json"
    )

    required_payloads = {
        "overview": overview,
        "quality": quality,
        "by_uf": by_uf,
        "by_occupation": by_occupation,
    }
    for name, payload in required_payloads.items():
        if str(payload.get("competence")) != yearmonth:
            raise ValueError(f"{name}: competência divergente.")

    if by_municipality is not None and str(
        by_municipality.get("competence")
    ) != yearmonth:
        raise ValueError("by_municipality: competência divergente.")

    release_admissions = int(overview["admissions"])
    release_dismissals = int(overview["dismissals"])
    release_balance = int(overview["balance"])
    if release_admissions - release_dismissals != release_balance:
        raise ValueError("overview: saldo inconsistente.")

    uf_items: list[dict[str, Any]] = []
    for raw in by_uf.get("items", []):
        item = _validate_metric_item(raw, label=f"UF {raw.get('uf')}")
        uf = str(item["uf"]).upper()
        if len(uf) != 2:
            raise ValueError(f"UF inválida: {uf!r}")
        uf_items.append(
            {
                "competence": competence,
                "uf": uf,
                "admissions": item["admissions"],
                "dismissals": item["dismissals"],
                "balance": item["balance"],
                "salary_mean_admissions": item.get("salary_mean_admissions"),
                "salary_median_admissions": item.get("salary_median_admissions"),
                "salary_mean_admissions_real": item.get(
                    "salary_mean_admissions_real"
                ),
                "salary_median_admissions_real": item.get(
                    "salary_median_admissions_real"
                ),
            }
        )

    occupation_items: list[dict[str, Any]] = []
    for raw in by_occupation.get("items", []):
        item = _validate_metric_item(raw, label=f"CBO {raw.get('cbo_codigo')}")
        cbo_family = str(item["cbo_familia"])
        cbo_code = str(item["cbo_codigo"])
        if len(cbo_family) != 4 or not cbo_family.isdigit():
            raise ValueError(f"Família CBO inválida: {cbo_family!r}")
        if not cbo_code.isdigit():
            raise ValueError(f"CBO inválida: {cbo_code!r}")
        occupation_items.append(
            {
                "competence": competence,
                "cbo_family": cbo_family,
                "cbo_code": cbo_code,
                "admissions": item["admissions"],
                "dismissals": item["dismissals"],
                "balance": item["balance"],
                "salary_mean_admissions": item.get("salary_mean_admissions"),
                "salary_median_admissions": item.get("salary_median_admissions"),
                "salary_mean_admissions_real": item.get(
                    "salary_mean_admissions_real"
                ),
                "salary_median_admissions_real": item.get(
                    "salary_median_admissions_real"
                ),
            }
        )

    municipality_items: list[dict[str, Any]] = []
    if by_municipality is not None:
        for raw in by_municipality.get("items", []):
            code = str(raw.get("municipio_codigo_caged") or "")
            item = _validate_metric_item(raw, label=f"Município {code}")
            if not code.isdigit():
                raise ValueError(f"Código municipal inválido: {code!r}")
            municipality_items.append(
                {
                    "competence": competence,
                    "municipality_code": code,
                    "admissions": item["admissions"],
                    "dismissals": item["dismissals"],
                    "balance": item["balance"],
                    "salary_mean_admissions": item.get("salary_mean_admissions"),
                    "salary_median_admissions": item.get(
                        "salary_median_admissions"
                    ),
                    "salary_mean_admissions_real": item.get(
                        "salary_mean_admissions_real"
                    ),
                    "salary_median_admissions_real": item.get(
                        "salary_median_admissions_real"
                    ),
                }
            )

    release = {
        "competence": competence,
        "source": str(overview.get("source") or "Novo CAGED / MTE"),
        "source_sha256": source_sha256,
        "publishable": True,
        "admissions": release_admissions,
        "dismissals": release_dismissals,
        "balance": release_balance,
        "records_tech": int(overview.get("records_tech") or 0),
        "salary_mean_admissions": overview.get("salary_mean_admissions"),
        "salary_median_admissions": overview.get("salary_median_admissions"),
        "salary_mean_admissions_real": overview.get(
            "salary_mean_admissions_real"
        ),
        "salary_median_admissions_real": overview.get(
            "salary_median_admissions_real"
        ),
        "salary_real_base_competence": overview.get(
            "salary_real_base_competence"
        ),
        "valid_rate": float(quality.get("valid_rate") or 0),
        "loaded_at_utc": datetime.now(UTC),
    }

    return ServingPayload(
        competence=competence,
        release=release,
        uf_items=tuple(uf_items),
        occupation_items=tuple(occupation_items),
        municipality_items=tuple(municipality_items),
    )


def load_serving_payload(engine: Engine, payload: ServingPayload) -> LoadResult:
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            delete(market_municipality).where(
                market_municipality.c.competence == payload.competence
            )
        )
        connection.execute(
            delete(market_occupation).where(
                market_occupation.c.competence == payload.competence
            )
        )
        connection.execute(
            delete(market_uf).where(market_uf.c.competence == payload.competence)
        )
        connection.execute(
            delete(dataset_release).where(
                dataset_release.c.competence == payload.competence
            )
        )

        connection.execute(insert(dataset_release), [payload.release])
        if payload.uf_items:
            connection.execute(insert(market_uf), list(payload.uf_items))
        if payload.occupation_items:
            connection.execute(insert(market_occupation), list(payload.occupation_items))
        if payload.municipality_items:
            connection.execute(
                insert(market_municipality),
                list(payload.municipality_items),
            )

        checks = {
            "UF": (
                market_uf,
                len(payload.uf_items),
            ),
            "CBO": (
                market_occupation,
                len(payload.occupation_items),
            ),
            "município": (
                market_municipality,
                len(payload.municipality_items),
            ),
        }
        for label, (table, expected) in checks.items():
            count = connection.scalar(
                select(func.count())
                .select_from(table)
                .where(table.c.competence == payload.competence)
            )
            if count != expected:
                raise RuntimeError(
                    f"Contagem pós-carga de {label} divergiu do payload."
                )

    return LoadResult(
        competence=payload.competence.strftime("%Y%m"),
        uf_rows=len(payload.uf_items),
        occupation_rows=len(payload.occupation_items),
        municipality_rows=len(payload.municipality_items),
        source_sha256=str(payload.release["source_sha256"]),
    )


def load_approved_release(
    *,
    database_url: str,
    yearmonth: str,
    bronze_dir: Path,
    gold_dir: Path,
    reference_path: Path,
    approvals_path: Path,
) -> LoadResult:
    gate = evaluate_publication_gate(
        yearmonth=yearmonth,
        bronze_dir=bronze_dir,
        gold_dir=gold_dir,
        reference_path=reference_path,
        approvals_path=approvals_path,
    )
    if not gate.publishable or not gate.source_sha256:
        raise ReleaseNotApprovedError(
            "Competência bloqueada pelo gate de publicação. "
            "Valide e aprove a metodologia antes da carga PostgreSQL."
        )

    payload = build_serving_payload(
        yearmonth=yearmonth,
        gold_dir=gold_dir,
        source_sha256=gate.source_sha256,
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        return load_serving_payload(engine, payload)
    finally:
        engine.dispose()
