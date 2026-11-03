"""Compare DuckDB releases using fictitious CAGED/RAIS Gold-shaped Parquet."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


def snapshot() -> dict:
    with tempfile.TemporaryDirectory(prefix="duckdb-parity-") as temp:
        root = Path(temp)
        caged = root / "market-synthetic.parquet"
        rais = root / "rais-market-synthetic.parquet"
        pq.write_table(pa.table({
            "uf": ["CE", "CE", "CE", "SP", "SP", "RJ"],
            "cbo_familia": [
                "Desenvolvimento", "Desenvolvimento", "Analise",
                "Desenvolvimento", "Analise", "Suporte",
            ],
            "cbo_codigo": ["212405", "212405", "212410", "212405", "212410", "317110"],
            "admissoes": [10, 5, 2, 20, 6, 1],
            "desligamentos": [3, 6, 4, 10, 2, 3],
            "saldo": [7, -1, -2, 10, 4, -2],
            "competencia": ["202608"] * 6,
        }), caged, compression="zstd")
        pq.write_table(pa.table({
            "year": [2025] * 5,
            "uf": ["CE", "CE", "SP", "SP", "RJ"],
            "cbo_familia": [
                "Desenvolvimento", "Analise", "Desenvolvimento", "Analise", "Suporte",
            ],
            "cbo_codigo": ["212405", "212410", "212405", "212410", "317110"],
            "active_stock": [150, 60, 200, 80, 20],
        }), rais, compression="zstd")

        connection = duckdb.connect(database=":memory:")
        def run(sql: str, paths: list[str]) -> list[list]:
            return [list(row) for row in connection.execute(sql, paths).fetchall()]

        try:
            by_uf = run("""
                SELECT uf, SUM(admissoes), SUM(desligamentos), SUM(saldo)
                FROM read_parquet(?) GROUP BY uf ORDER BY uf
            """, [str(caged)])
            assert by_uf == [
                ["CE", 17, 13, 4], ["RJ", 1, 3, -2], ["SP", 26, 12, 14],
            ], by_uf

            stock_flow = run("""
                WITH c AS (
                    SELECT uf, cbo_codigo, SUM(saldo) AS saldo
                    FROM read_parquet(?) GROUP BY uf, cbo_codigo
                ), r AS (
                    SELECT uf, cbo_codigo, SUM(active_stock) AS active_stock
                    FROM read_parquet(?) WHERE year=2025 GROUP BY uf, cbo_codigo
                )
                SELECT c.uf, c.cbo_codigo, c.saldo, r.active_stock
                FROM c INNER JOIN r USING (uf, cbo_codigo)
                ORDER BY c.uf, c.cbo_codigo
            """, [str(caged), str(rais)])
            assert len(stock_flow) == 5, stock_flow

            ranking = run("""
                SELECT uf, cbo_familia, SUM(saldo) AS saldo,
                       ROW_NUMBER() OVER (
                           PARTITION BY uf ORDER BY SUM(saldo) DESC, cbo_familia
                       ) AS rank
                FROM read_parquet(?) GROUP BY uf, cbo_familia
                ORDER BY uf, rank
            """, [str(caged)])
            assert len(ranking) == 5, ranking
            return {"by_uf": by_uf, "stock_flow": stock_flow, "ranking": ranking}
        finally:
            connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--compare", type=Path, nargs=2, metavar=("BASE", "CANDIDATE"))
    args = parser.parse_args()
    if args.compare:
        first, second = [
            json.loads(path.read_text(encoding="utf-8")) for path in args.compare
        ]
        if first != second:
            raise SystemExit("DuckDB 1.5.6 and 2.0.0 synthetic Gold outputs differ")
        print("DuckDB 1.5.6 and 2.0.0 synthetic Gold SQL parity: OK")
    else:
        args.output.write_text(
            json.dumps(snapshot(), sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"DuckDB {duckdb.__version__} synthetic snapshot: OK")


if __name__ == "__main__":
    main()
