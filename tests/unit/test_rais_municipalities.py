from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.validation.rais_municipalities import (
    RESIDUAL_MUNICIPALITY_CODE,
    validate_rais_municipalities,
)


def test_rais_municipalities_match_ibge_prefixes(tmp_path: Path):
    silver = tmp_path / "rais.parquet"
    pq.write_table(
        pa.table(
            {
                "municipio_codigo": [
                    "230440",
                    "355030",
                    RESIDUAL_MUNICIPALITY_CODE,
                ],
                "uf": ["CE", "SP", "NI"],
            }
        ),
        silver,
    )

    result = validate_rais_municipalities(
        silver_path=silver,
        ibge_codes={"2304400", "3550308"},
        year=2025,
    )

    assert result.silver_rows == 3
    assert result.unique_codes == 3
    assert result.residual_rows == 1
    assert result.matched_codes == 2
    assert result.unmatched_codes == ()
    assert result.uf_mismatch_rows == 0
    assert result.municipality_ready is True


def test_rais_municipalities_block_unknown_code(tmp_path: Path):
    silver = tmp_path / "rais.parquet"
    pq.write_table(
        pa.table(
            {
                "municipio_codigo": ["230440", "990001"],
                "uf": ["CE", "NI"],
            }
        ),
        silver,
    )

    result = validate_rais_municipalities(
        silver_path=silver,
        ibge_codes={"2304400"},
        year=2025,
    )

    assert result.unmatched_codes == ("990001",)
    assert result.municipality_ready is False


def test_rais_municipalities_block_uf_mismatch(tmp_path: Path):
    silver = tmp_path / "rais.parquet"
    pq.write_table(
        pa.table(
            {
                "municipio_codigo": ["230440"],
                "uf": ["SP"],
            }
        ),
        silver,
    )

    result = validate_rais_municipalities(
        silver_path=silver,
        ibge_codes={"2304400"},
        year=2025,
    )

    assert result.uf_mismatch_rows == 1
    assert result.municipality_ready is False
