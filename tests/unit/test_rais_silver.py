import json
from pathlib import Path

import pyarrow.parquet as pq

from src.transform.rais_silver import (
    normalize_cbo_code,
    transform_rais_year,
    uf_from_municipality_code,
)


def _prepare_reports(base: Path) -> tuple[Path, Path, Path]:
    layout = base / "layout-report.json"
    semantic = base / "semantic-layout-report.json"
    values = base / "value-semantics-report.json"

    layout.write_text(
        json.dumps(
            {
                "year": 2025,
                "files": [
                    {
                        "file": "RAIS_VINC_TESTE.COMT",
                        "encoding": "utf-8",
                        "delimiter": ",",
                        "columns": [
                            "CBO 2002 Ocupação - Código",
                            "Município - Código",
                            "Ind Vínculo Ativo 31/12 - Código",
                        ],
                        "normalized_columns": [
                            "cbo_2002_ocupacao_codigo",
                            "municipio_codigo",
                            "ind_vinculo_ativo_31_12_codigo",
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    semantic.write_text(
        json.dumps(
            {
                "year": 2025,
                "silver_ready": True,
                "files": [
                    {
                        "file": "RAIS_VINC_TESTE.COMT",
                        "valid": True,
                        "required": {
                            "cbo_occupation": {
                                "status": "matched",
                                "matches": ["cbo_2002_ocupacao_codigo"],
                            },
                            "municipality": {
                                "status": "matched",
                                "matches": ["municipio_codigo"],
                            },
                            "active_3112": {
                                "status": "matched",
                                "matches": ["ind_vinculo_ativo_31_12_codigo"],
                            },
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    values.write_text(
        json.dumps(
            {
                "year": 2025,
                "silver_transform_ready": True,
                "active_3112": {
                    "official_active_values": ["1"],
                    "official_inactive_values": ["0"],
                },
            }
        ),
        encoding="utf-8",
    )
    return layout, semantic, values


def test_cbo_and_uf_normalization():
    assert normalize_cbo_code("212405") == "212405"
    assert normalize_cbo_code("12345") == "012345"
    assert normalize_cbo_code("1234") is None
    assert uf_from_municipality_code("230440") == "CE"
    assert uf_from_municipality_code("355030") == "SP"
    assert uf_from_municipality_code("330455") == "RJ"
    assert uf_from_municipality_code("990000") is None


def test_transform_rais_year_filters_active_and_tech(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.COMT").write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código\n"
        "212405,230440,1\n"
        "317110,355030,0\n"
        "411010,330455,1\n"
        "212405,230440,1\n",
        encoding="utf-8",
    )
    layout, semantic, values = _prepare_reports(tmp_path)
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        'families:\n  "2124": "Analistas de tecnologia da informação"\n'
        '  "3171": "Técnicos de desenvolvimento"\n',
        encoding="utf-8",
    )

    result = transform_rais_year(
        year=2025,
        extracted_dir=extracted,
        layout_report_path=layout,
        semantic_report_path=semantic,
        value_semantics_report_path=values,
        cbo_config_path=cbo,
        silver_dir=silver,
        batch_size=1000,
    )

    assert result.rows_read == 4
    assert result.rows_valid == 4
    assert result.rows_active == 3
    assert result.rows_inactive == 1
    assert result.rows_active_source == 3
    assert result.rows_inactive_source == 1
    assert result.rows_unknown_status_source == 0
    assert result.rows_year_mismatch_source == 0
    assert result.rows_tech == 2
    assert result.rows_rejected == 0

    table = pq.read_table(result.silver_path)
    assert table.num_rows == 2
    assert set(table.column("cbo_familia").to_pylist()) == {"2124"}
    assert set(table.column("uf").to_pylist()) == {"CE"}
    assert set(table.column("municipio_codigo").to_pylist()) == {"230440"}


def test_transform_rais_year_preserves_rejections(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.COMT").write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código\n"
        "212405,230440,1\n"
        "xx,990000,9\n",
        encoding="utf-8",
    )
    layout, semantic, values = _prepare_reports(tmp_path)
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        'families:\n  "2124": "Analistas de tecnologia da informação"\n',
        encoding="utf-8",
    )

    result = transform_rais_year(
        year=2025,
        extracted_dir=extracted,
        layout_report_path=layout,
        semantic_report_path=semantic,
        value_semantics_report_path=values,
        cbo_config_path=cbo,
        silver_dir=silver,
        batch_size=1000,
    )

    assert result.rows_rejected == 1
    assert result.rows_active_source == 1
    assert result.rows_inactive_source == 0
    assert result.rows_unknown_status_source == 1
    assert result.rows_year_mismatch_source == 0
    rejected = pq.read_table(result.reject_path).to_pylist()
    assert len(rejected) == 1
    assert "invalid_active_status" in rejected[0]["reason"]
    assert "invalid_cbo" in rejected[0]["reason"]
    assert "invalid_uf" in rejected[0]["reason"]

    quality = json.loads(result.quality_path.read_text(encoding="utf-8"))
    assert quality["source_partition_complete"] is True
    assert quality["year_source"] == "annual_context"
    assert quality["uf_source"] == "municipality_code_prefix"
    assert quality["gold_ready"] is False
    assert quality["publication_ready"] is False


def test_transform_rais_year_requires_value_semantics_ready(tmp_path: Path):
    layout, semantic, values = _prepare_reports(tmp_path)
    payload = json.loads(values.read_text(encoding="utf-8"))
    payload["silver_transform_ready"] = False
    values.write_text(json.dumps(payload), encoding="utf-8")

    cbo = tmp_path / "cbo.yml"
    cbo.write_text('families:\n  "2124": "Tech"\n', encoding="utf-8")

    try:
        transform_rais_year(
            year=2025,
            extracted_dir=tmp_path,
            layout_report_path=layout,
            semantic_report_path=semantic,
            value_semantics_report_path=values,
            cbo_config_path=cbo,
            silver_dir=tmp_path / "silver",
        )
    except ValueError as exc:
        assert "Semântica de valores RAIS" in str(exc)
    else:
        raise AssertionError("Silver deveria permanecer bloqueado.")
