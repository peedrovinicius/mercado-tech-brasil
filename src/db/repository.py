from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.engine import Connection

from src.db.schema import (
    dataset_release,
    market_municipality,
    market_occupation,
    market_uf,
)


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def _float_or_none(value: Any) -> float | None:
    return float(value) if value is not None else None


def _latest_release(connection: Connection) -> dict[str, Any] | None:
    row = connection.execute(
        select(dataset_release)
        .where(dataset_release.c.publishable.is_(True))
        .order_by(dataset_release.c.competence.desc())
        .limit(1)
    ).mappings().first()
    return dict(row) if row else None


def _salary_payload(row: Any) -> dict[str, object]:
    return {
        "salary_mean_admissions": _float_or_none(
            row.get("salary_mean_admissions")
        ),
        "salary_median_admissions": _float_or_none(
            row.get("salary_median_admissions")
        ),
        "salary_mean_admissions_real": _float_or_none(
            row.get("salary_mean_admissions_real")
        ),
        "salary_median_admissions_real": _float_or_none(
            row.get("salary_median_admissions_real")
        ),
    }


def fetch_overview(database_url: str) -> dict[str, object] | None:
    engine = get_engine(database_url)
    with engine.connect() as connection:
        release = _latest_release(connection)
        if release is None:
            return None
        return {
            "competence": release["competence"].strftime("%Y%m"),
            "scope": "recorte CBO de tecnologia versionado",
            "admissions": release["admissions"],
            "dismissals": release["dismissals"],
            "balance": release["balance"],
            **_salary_payload(release),
            "salary_real_base_competence": release.get(
                "salary_real_base_competence"
            ),
            "records_tech": release["records_tech"],
            "source": release["source"],
            "status": "served_from_postgresql",
        }


def fetch_by_uf(
    database_url: str,
    *,
    limit: int,
) -> dict[str, object] | None:
    engine = get_engine(database_url)
    with engine.connect() as connection:
        release = _latest_release(connection)
        if release is None:
            return None
        rows = connection.execute(
            select(market_uf)
            .where(market_uf.c.competence == release["competence"])
            .order_by(market_uf.c.admissions.desc(), market_uf.c.uf.asc())
            .limit(limit)
        ).mappings().all()
        items = [
            {
                "uf": row["uf"],
                "admissions": row["admissions"],
                "dismissals": row["dismissals"],
                "balance": row["balance"],
                **_salary_payload(row),
            }
            for row in rows
        ]
        return {
            "competence": release["competence"].strftime("%Y%m"),
            "source": release["source"],
            "salary_real_base_competence": release.get(
                "salary_real_base_competence"
            ),
            "items": items,
        }


def fetch_by_occupation(
    database_url: str,
    *,
    limit: int,
) -> dict[str, object] | None:
    engine = get_engine(database_url)
    with engine.connect() as connection:
        release = _latest_release(connection)
        if release is None:
            return None
        rows = connection.execute(
            select(market_occupation)
            .where(market_occupation.c.competence == release["competence"])
            .order_by(
                market_occupation.c.admissions.desc(),
                market_occupation.c.cbo_code.asc(),
            )
            .limit(limit)
        ).mappings().all()
        items = [
            {
                "cbo_familia": row["cbo_family"],
                "cbo_codigo": row["cbo_code"],
                "admissions": row["admissions"],
                "dismissals": row["dismissals"],
                "balance": row["balance"],
                **_salary_payload(row),
            }
            for row in rows
        ]
        return {
            "competence": release["competence"].strftime("%Y%m"),
            "source": release["source"],
            "salary_real_base_competence": release.get(
                "salary_real_base_competence"
            ),
            "items": items,
        }


def fetch_by_municipality(
    database_url: str,
    *,
    limit: int,
) -> dict[str, object] | None:
    engine = get_engine(database_url)
    with engine.connect() as connection:
        release = _latest_release(connection)
        if release is None:
            return None

        rows = connection.execute(
            select(market_municipality)
            .where(market_municipality.c.competence == release["competence"])
            .order_by(
                market_municipality.c.admissions.desc(),
                market_municipality.c.municipality_code.asc(),
            )
            .limit(limit)
        ).mappings().all()

        if not rows:
            return None

        items = [
            {
                "municipio_codigo_caged": row["municipality_code"],
                "municipio_codigo_ibge": row["municipality_ibge_code"],
                "municipio_nome": row["municipality_name"],
                "uf": row["uf"],
                "admissions": row["admissions"],
                "dismissals": row["dismissals"],
                "balance": row["balance"],
                "population_estimate": row["population_estimate"],
                "population_reference_year": row["population_reference_year"],
                "admissions_per_100k": _float_or_none(
                    row["admissions_per_100k"]
                ),
                "dismissals_per_100k": _float_or_none(
                    row["dismissals_per_100k"]
                ),
                "balance_per_100k": _float_or_none(
                    row["balance_per_100k"]
                ),
                **_salary_payload(row),
            }
            for row in rows
        ]
        population_years = {
            int(item["population_reference_year"])
            for item in items
            if item["population_reference_year"] is not None
        }
        return {
            "competence": release["competence"].strftime("%Y%m"),
            "source": release["source"],
            "code_system": "codigo_municipio_caged",
            "salary_real_base_competence": release.get(
                "salary_real_base_competence"
            ),
            "population_source": "IBGE SIDRA" if population_years else None,
            "population_reference_year": (
                next(iter(population_years))
                if len(population_years) == 1
                else None
            ),
            "items": items,
        }


def fetch_trend(database_url: str) -> dict[str, object] | None:
    engine = get_engine(database_url)
    with engine.connect() as connection:
        rows = connection.execute(
            select(dataset_release)
            .where(dataset_release.c.publishable.is_(True))
            .order_by(dataset_release.c.competence.asc())
        ).mappings().all()

        if not rows:
            return None

        items = [
            {
                "competence": row["competence"].strftime("%Y%m"),
                "admissions": row["admissions"],
                "dismissals": row["dismissals"],
                "balance": row["balance"],
                **_salary_payload(row),
                "salary_real_base_competence": row.get(
                    "salary_real_base_competence"
                ),
            }
            for row in rows
        ]
        return {
            "source": "Novo CAGED / MTE",
            "scope": "recorte CBO de tecnologia versionado",
            "items": items,
        }
