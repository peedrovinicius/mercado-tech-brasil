"""Synthetic-only snapshots to verify Polars 1.30/2.0 CAGED and RAIS parity."""
from __future__ import annotations

import argparse
import difflib
import json
import tempfile
from pathlib import Path


def normalized(value):
    if isinstance(value, dict):
        return {key: normalized(val) for key, val in sorted(value.items())}
    if isinstance(value, list):
        items = [normalized(item) for item in value]
        if all(isinstance(item, dict) for item in items):
            return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return items
    return value


def snapshot():
    import polars as pl
    from src.gold.aggregate import build_gold
    from src.gold.rais import build_rais_gold
    from src.transform.adjustments import add_adjustment_deltas
    from src.transform.caged import transform_mov_file

    def read_json(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def rows(path):
        return pl.read_parquet(path).to_dicts()

    with tempfile.TemporaryDirectory(prefix="polars-compat-") as temp:
        root = Path(temp)
        config = Path("config/cbo_tech.yml")
        source = root / "CAGEDMOV_SYNTHETIC.txt"
        source.write_text(
            "competência Mov;UF;Município;saldo movimentação;CBO 2002 Ocupação;"
            "tipo movimentação;salário;Ind Trab Intermitente\n"
            "202607;23;230440;1;212405;10;4500,00;0\n"
            "202607;23;230440;-1;212405;31;4200,00;0\n"
            "202607;35;355030;1;317110;10;6000,00;0\n"
            "202607;35;355030;1;513440;10;1900,00;0\n"
            "202607;99;999999;1;212405;10;3500,00;0\n"
            "202607;23;230440;1;212405;10;400,00;0\n"
            "202607;23;230440;1;212405;10;8000,00;1\n"
            "202607;77;777777;1;212405;10;8000,00;0\n"
            "202607;23;230440;1;XX;10;8000,00;0\n",
            encoding="utf-8",
        )
        silver, gold = root / "silver", root / "gold"
        result = transform_mov_file(
            source, yearmonth="202607", silver_dir=silver,
            gold_dir=gold, cbo_config_path=config,
        )
        assert (result.rows_read, result.rows_valid, result.rows_rejected, result.rows_tech) == (9, 7, 2, 6)
        first = (
            pl.read_parquet(result.silver_path)
            .filter((pl.col("uf") == "CE") & (pl.col("saldo_movimentacao") == 1))
            .head(1)
        )
        for kind, suffix in (("FOR", "for_202607"), ("EXC", "exc_202609")):
            (
                add_adjustment_deltas(first, kind=kind)
                .with_columns(pl.lit("202607").alias("effective_competence"))
                .write_parquet(silver / f"caged_tech_{suffix}.parquet")
            )
        market, overview_path = build_gold(result.silver_path, yearmonth="202607", gold_dir=gold)
        overview = read_json(overview_path)
        assert (overview["admissions"], overview["dismissals"], overview["balance"]) == (5, 1, 4)
        assert overview["salary_eligible_admissions"] == 3

        rais_silver = root / "rais_synthetic.parquet"
        pl.DataFrame({
            "year": [2025] * 5,
            "uf": ["CE", "CE", "SP", "NI", "CE"],
            "cbo_familia": ["2124", "2124", "3171", "2124", "3171"],
            "cbo_codigo": ["212405", "212405", "317110", "212405", "317110"],
            "active_3112": [True] * 5,
        }).write_parquet(rais_silver)
        reconciliation = root / "rais_reconciliation_synthetic.json"
        reconciliation.write_text(json.dumps({
            "year": 2025, "reconciled": True, "gold_ready": True,
            "expected_active": 12, "difference": 0, "source": "synthetic-test",
        }), encoding="utf-8")
        rais = build_rais_gold(
            year=2025, silver_path=rais_silver, reconciliation_path=reconciliation,
            cbo_config_path=config, gold_dir=root / "rais_gold",
        )
        assert read_json(rais["overview"])["active_stock_tech"] == 5
        assert read_json(rais["overview"])["market_rows"] == 4

        return normalized({
            "caged": {
                "counts": [result.rows_read, result.rows_valid, result.rows_rejected, result.rows_tech],
                "quality": read_json(result.quality_path),
                "national_audit": read_json(gold / "audit-national-mov-202607.json"),
                "silver": rows(result.silver_path),
                "rejected": rows(result.reject_path),
                "market": rows(market),
                "overview": overview,
                "by_uf": read_json(gold / "by-uf-202607.json"),
                "by_occupation": read_json(gold / "by-occupation-202607.json"),
                "by_municipality": read_json(gold / "by-municipality-202607.json"),
                "trend": read_json(gold / "trend.json"),
            },
            "rais": {
                "market": rows(rais["market"]),
                "overview": read_json(rais["overview"]),
                "by_uf": read_json(rais["by_uf"]),
                "by_cbo_family": read_json(rais["by_cbo_family"]),
            },
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--compare", type=Path, nargs=2, metavar=("POLARS_1", "POLARS_2"))
    args = parser.parse_args()
    if args.output:
        args.output.write_text(
            json.dumps(snapshot(), sort_keys=True, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Generated synthetic CAGED/RAIS snapshot: {args.output}")
    else:
        before = args.compare[0].read_text(encoding="utf-8").splitlines(keepends=True)
        after = args.compare[1].read_text(encoding="utf-8").splitlines(keepends=True)
        if before != after:
            print("".join(difflib.unified_diff(before, after)))
            raise SystemExit("FAIL: Polars 1.x/2.0 synthetic CAGED/RAIS outputs differ")
        print("PASS: Polars 1.x/2.0 synthetic CAGED/RAIS outputs are identical")


if __name__ == "__main__":
    main()
