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
                            "Ind Vínculo Abandonado - Código",
                        ],
                        "normalized_columns": [
                            "cbo_2002_ocupacao_codigo",
                            "municipio_codigo",
                            "ind_vinculo_ativo_31_12_codigo",
                            "ind_vinculo_abandonado_codigo",
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
                            "abandoned_link": {
                                "status": "matched",
                                "matches": ["ind_vinculo_abandonado_codigo"],
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
                "abandoned_link": {
                    "official_eligible_values": ["0"],
                    "official_excluded_values": ["1"],
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
    assert uf_from_municipality_code("999999") == "NI"


def test_transform_filters_abandoned_from_official_stock_and_tech(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.COMT").write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código,Ind Vínculo Abandonado - Código\n"
        "212405,230440,1,0\n"
        "317110,355030,0,0\n"
        "411010,330455,1,0\n"
        "212405,230440,1,1\n"
        "212405,230440,1,0\n",
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

    assert result.rows_read == 5
    assert result.rows_active_source == 4
    assert result.rows_abandoned_source == 1
    assert result.rows_stock_eligible_source == 3
    assert result.rows_unknown_abandoned_source == 0
    assert result.rows_inactive_source == 1
    assert result.rows_active == 3
    assert result.rows_inactive == 1
    assert result.rows_tech == 2
    assert result.rows_rejected == 0

    table = pq.read_table(result.silver_path)
    assert table.num_rows == 2
    assert set(table.column("cbo_familia").to_pylist()) == {"2124"}

    quality = json.loads(result.quality_path.read_text(encoding="utf-8"))
    assert quality["stock_partition_complete"] is True
    assert quality["stock_rule"] == "active_3112=1 and abandoned_link=0"


def test_transform_preserves_residual_municipality(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.COMT").write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código,Ind Vínculo Abandonado - Código\n"
        "212405,999999,1,0\n",
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

    assert result.rows_rejected == 0
    assert result.rows_residual_municipality == 1
    assert result.rows_stock_eligible_source == 1
    assert pq.read_table(result.silver_path).to_pylist()[0]["uf"] == "NI"


def test_transform_rejects_unknown_stock_status(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.COMT").write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código,Ind Vínculo Abandonado - Código\n"
        "212405,230440,1,0\n"
        "xx,990000,9,9\n",
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
    rejected = pq.read_table(result.reject_path).to_pylist()
    assert "invalid_active_status" in rejected[0]["reason"]
    assert "invalid_abandoned_status" in rejected[0]["reason"]
    assert "invalid_cbo" in rejected[0]["reason"]
    assert rejected[0]["abandoned_raw"] == "9"
