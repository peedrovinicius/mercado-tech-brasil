import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

from src.db.loader import (
    ReleaseNotApprovedError,
    build_serving_payload,
    load_approved_release,
    load_serving_payload,
)
from src.db.repository import fetch_by_occupation, fetch_by_uf, fetch_overview
from src.db.schema import dataset_release, market_occupation, market_uf

YEAR_MONTH = "202607"
SOURCE_SHA = "a" * 64


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fixture(tmp_path: Path, *, approved: bool) -> tuple[Path, Path, Path, Path]:
    bronze = tmp_path / "bronze"
    gold = tmp_path / "gold"
    reference = tmp_path / "reference.json"
    approvals = tmp_path / "approvals.json"

    _write_json(
        bronze / YEAR_MONTH / "extracted" / "CAGEDMOV.txt.manifest.json",
        {
            "source": "novo_caged_mov_local",
            "competence": YEAR_MONTH,
            "original_name": "CAGEDMOV202607.txt",
            "size_bytes": 100,
            "sha256": SOURCE_SHA,
            "ingested_at_utc": "2026-09-25T20:00:00+00:00",
        },
    )
    _write_json(
        gold / f"quality-{YEAR_MONTH}.json",
        {
            "competence": YEAR_MONTH,
            "rows_read": 4,
            "rows_valid": 4,
            "rows_rejected": 0,
            "rows_tech": 4,
            "valid_rate": 1.0,
        },
    )
    _write_json(
        gold / f"overview-{YEAR_MONTH}.json",
        {
            "competence": YEAR_MONTH,
            "admissions": 3,
            "dismissals": 1,
            "balance": 2,
            "records_tech": 4,
            "salary_mean_admissions": 5200,
            "salary_median_admissions": 5000,
            "source": "Novo CAGED / MTE",
        },
    )
    _write_json(
        gold / f"by-uf-{YEAR_MONTH}.json",
        {
            "competence": YEAR_MONTH,
            "source": "Novo CAGED / MTE",
            "items": [
                {
                    "uf": "CE",
                    "admissions": 2,
                    "dismissals": 1,
                    "balance": 1,
                    "salary_median_admissions": 4500,
                },
                {
                    "uf": "SP",
                    "admissions": 1,
                    "dismissals": 0,
                    "balance": 1,
                    "salary_median_admissions": 6000,
                },
            ],
        },
    )
    _write_json(
        gold / f"by-occupation-{YEAR_MONTH}.json",
        {
            "competence": YEAR_MONTH,
            "source": "Novo CAGED / MTE",
            "items": [
                {
                    "cbo_familia": "2124",
                    "cbo_codigo": "212405",
                    "admissions": 2,
                    "dismissals": 1,
                    "balance": 1,
                    "salary_median_admissions": 5000,
                },
                {
                    "cbo_familia": "3171",
                    "cbo_codigo": "317110",
                    "admissions": 1,
                    "dismissals": 0,
                    "balance": 1,
                    "salary_median_admissions": 6000,
                },
            ],
        },
    )
    _write_json(
        gold / f"by-municipality-{YEAR_MONTH}.json",
        {
            "competence": YEAR_MONTH,
            "source": "Novo CAGED / MTE",
            "items": [
                {
                    "municipio_codigo_caged": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "admissions": 2,
                    "dismissals": 1,
                    "balance": 1,
                    "salary_median_admissions": 4500,
                },
                {
                    "municipio_codigo_caged": "355030",
                    "municipio_codigo_ibge": "3550308",
                    "municipio_nome": "São Paulo",
                    "uf": "SP",
                    "admissions": 1,
                    "dismissals": 0,
                    "balance": 1,
                    "salary_median_admissions": 6000,
                },
            ],
        },
    )
    (gold / f"market-{YEAR_MONTH}.parquet").write_bytes(b"placeholder")
    _write_json(
        gold / f"audit-national-mov-{YEAR_MONTH}.json",
        {
            "competence": YEAR_MONTH,
            "admissions": 3,
            "dismissals": 1,
            "balance": 2,
            "non_identified": {
                "admissions": 0,
                "dismissals": 0,
                "balance": 0,
            },
        },
    )
    _write_json(
        reference,
        {
            YEAR_MONTH: {
                "admissoes": 3,
                "desligamentos": 1,
                "saldo": 2,
            }
        },
    )
    _write_json(
        approvals,
        (
            {
                YEAR_MONTH: {
                    "approved": True,
                    "reviewer": "test",
                    "notes": "reviewed",
                    "source_sha256": SOURCE_SHA,
                }
            }
            if approved
            else {}
        ),
    )
    return bronze, gold, reference, approvals


def test_serving_load_is_idempotent_and_queryable(tmp_path: Path):
    _, gold, _, _ = _fixture(tmp_path, approved=True)
    payload = build_serving_payload(
        yearmonth=YEAR_MONTH,
        gold_dir=gold,
        source_sha256=SOURCE_SHA,
    )
    database_url = f"sqlite+pysqlite:///{tmp_path / 'serving.db'}"
    engine = create_engine(database_url)

    first = load_serving_payload(engine, payload)
    second = load_serving_payload(engine, payload)

    assert first.uf_rows == second.uf_rows == 2
    assert first.occupation_rows == second.occupation_rows == 2
    assert fetch_overview(database_url)["salary_median_admissions"] == 5000.0
    assert len(fetch_by_uf(database_url, limit=27)["items"]) == 2
    assert len(fetch_by_occupation(database_url, limit=10)["items"]) == 2

    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(dataset_release)) == 1
        assert connection.scalar(select(func.count()).select_from(market_uf)) == 2
        assert connection.scalar(select(func.count()).select_from(market_occupation)) == 2


def test_load_approved_release_blocks_without_approval(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path, approved=False)
    database_url = f"sqlite+pysqlite:///{tmp_path / 'blocked.db'}"

    with pytest.raises(ReleaseNotApprovedError):
        load_approved_release(
            database_url=database_url,
            yearmonth=YEAR_MONTH,
            bronze_dir=bronze,
            gold_dir=gold,
            reference_path=reference,
            approvals_path=approvals,
        )


def test_load_approved_release_accepts_sha_bound_approval(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path, approved=True)
    database_url = f"sqlite+pysqlite:///{tmp_path / 'approved.db'}"

    result = load_approved_release(
        database_url=database_url,
        yearmonth=YEAR_MONTH,
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )

    assert result.competence == YEAR_MONTH
    assert result.source_sha256 == SOURCE_SHA
    assert fetch_overview(database_url)["balance"] == 2
