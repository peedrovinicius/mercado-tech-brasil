import json
from pathlib import Path

import polars as pl

from src.gold.rais import build_rais_gold


def _write_reconciliation(
    path: Path,
    *,
    reconciled: bool = True,
    gold_ready: bool = True,
) -> None:
    path.write_text(
        json.dumps(
            {
                "year": 2025,
                "expected_active": 1000,
                "observed_active": 1000,
                "difference": 0,
                "reconciled": reconciled,
                "gold_ready": gold_ready,
                "publication_ready": False,
                "source": "RAIS 2025 / MTE",
                "source_url": "https://example.invalid/official",
            }
        ),
        encoding="utf-8",
    )


def _write_silver(path: Path) -> None:
    pl.DataFrame(
        {
            "year": [2025, 2025, 2025, 2025],
            "cbo_codigo": ["212405", "212405", "317110", "212310"],
            "cbo_familia": ["2124", "2124", "3171", "2123"],
            "municipio_codigo": [
                "2304400",
                "2304400",
                "3550308",
                "3304557",
            ],
            "uf": ["CE", "CE", "SP", "RJ"],
            "active_3112": [True, True, True, True],
            "source_file": ["a.comt", "a.comt", "b.comt", "c.comt"],
        }
    ).write_parquet(path)


def _write_cbo(path: Path) -> None:
    path.write_text(
        'version: 2\n'
        'families:\n'
        '  "2123": "Administradores de tecnologia da informação"\n'
        '  "2124": "Analistas de tecnologia da informação"\n'
        '  "3171": "Técnicos de desenvolvimento de sistemas e aplicações"\n',
        encoding="utf-8",
    )


def test_build_rais_gold_creates_annual_aggregates(tmp_path: Path):
    silver = tmp_path / "rais_tech_2025.parquet"
    reconciliation = tmp_path / "rais_reconciliation_2025.json"
    cbo = tmp_path / "cbo.yml"
    gold = tmp_path / "gold"

    _write_silver(silver)
    _write_reconciliation(reconciliation)
    _write_cbo(cbo)

    paths = build_rais_gold(
        year=2025,
        silver_path=silver,
        reconciliation_path=reconciliation,
        cbo_config_path=cbo,
        gold_dir=gold,
    )

    overview = json.loads(paths["overview"].read_text(encoding="utf-8"))
    assert overview["active_stock_tech"] == 4
    assert overview["active_stock_national_reference"] == 1000
    assert overview["share_tech_of_national_active"] == 0.004
    assert overview["publication_ready"] is False
    assert overview["status"] == "generated_not_published"

    by_uf = json.loads(paths["by_uf"].read_text(encoding="utf-8"))
    assert by_uf["items"][0] == {
        "uf": "CE",
        "active_stock": 2,
        "share_of_tech_stock": 0.5,
    }

    by_family = json.loads(
        paths["by_cbo_family"].read_text(encoding="utf-8")
    )
    assert by_family["items"][0]["cbo_familia"] == "2124"
    assert by_family["items"][0]["active_stock"] == 2

    market = pl.read_parquet(paths["market"])
    assert market.get_column("active_stock").sum() == 4


def test_build_rais_gold_requires_successful_reconciliation(tmp_path: Path):
    silver = tmp_path / "rais_tech_2025.parquet"
    reconciliation = tmp_path / "rais_reconciliation_2025.json"
    cbo = tmp_path / "cbo.yml"

    _write_silver(silver)
    _write_reconciliation(
        reconciliation,
        reconciled=False,
        gold_ready=False,
    )
    _write_cbo(cbo)

    try:
        build_rais_gold(
            year=2025,
            silver_path=silver,
            reconciliation_path=reconciliation,
            cbo_config_path=cbo,
            gold_dir=tmp_path / "gold",
        )
    except ValueError as exc:
        assert "reconciliada" in str(exc)
    else:
        raise AssertionError("Gold RAIS deveria permanecer bloqueado.")


def test_build_rais_gold_rejects_inactive_rows(tmp_path: Path):
    silver = tmp_path / "rais_tech_2025.parquet"
    reconciliation = tmp_path / "rais_reconciliation_2025.json"
    cbo = tmp_path / "cbo.yml"

    _write_silver(silver)
    frame = pl.read_parquet(silver).with_columns(
        pl.when(pl.arange(0, pl.len()) == 0)
        .then(pl.lit(False))
        .otherwise(pl.col("active_3112"))
        .alias("active_3112")
    )
    frame.write_parquet(silver)
    _write_reconciliation(reconciliation)
    _write_cbo(cbo)

    try:
        build_rais_gold(
            year=2025,
            silver_path=silver,
            reconciliation_path=reconciliation,
            cbo_config_path=cbo,
            gold_dir=tmp_path / "gold",
        )
    except ValueError as exc:
        assert "não ativo" in str(exc)
    else:
        raise AssertionError("Gold não deve aceitar vínculo inativo.")
