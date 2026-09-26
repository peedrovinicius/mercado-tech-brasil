import json
from pathlib import Path

import pyarrow.parquet as pq

from src.transform.rais_silver import transform_rais_year


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
                        "file": "RAIS_VINC_TESTE.comt",
                        "encoding": "utf-8",
                        "delimiter": ";",
                        "columns": [
                            "Ano",
                            "CBO Ocupação 2002",
                            "Município",
                            "UF",
                            "Vínculo Ativo 31/12",
                        ],
                        "normalized_columns": [
                            "ano",
                            "cbo_ocupacao_2002",
                            "municipio",
                            "uf",
                            "vinculo_ativo_31_12",
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
                        "file": "RAIS_VINC_TESTE.comt",
                        "valid": True,
                        "required": {
                            "year": {"status": "matched", "matches": ["ano"]},
                            "cbo_occupation": {
                                "status": "matched",
                                "matches": ["cbo_ocupacao_2002"],
                            },
                            "municipality": {
                                "status": "matched",
                                "matches": ["municipio"],
                            },
                            "uf": {"status": "matched", "matches": ["uf"]},
                            "active_3112": {
                                "status": "matched",
                                "matches": ["vinculo_ativo_31_12"],
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
                    "official_active_values": ["sim"],
                    "official_inactive_values": ["nao"],
                },
            }
        ),
        encoding="utf-8",
    )
    return layout, semantic, values


def test_transform_rais_year_filters_active_and_tech(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.comt").write_text(
        "Ano;CBO Ocupação 2002;Município;UF;Vínculo Ativo 31/12\n"
        "2025;212405;2304400;CE;SIM\n"
        "2025;317110;3550308;SP;NÃO\n"
        "2025;411010;3304557;RJ;SIM\n"
        "2025;212405;2304400;CE;SIM\n",
        encoding="utf-8",
    )
    layout, semantic, values = _prepare_reports(tmp_path)
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        'families:\n  "2122": "Engenheiros em computação"\n'
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
    assert set(table.column("cbo_familia").to_pylist()) == {"2122"}


def test_transform_rais_year_preserves_rejections(tmp_path: Path):
    extracted = tmp_path / "extracted"
    silver = tmp_path / "silver"
    extracted.mkdir()

    (extracted / "RAIS_VINC_TESTE.comt").write_text(
        "Ano;CBO Ocupação 2002;Município;UF;Vínculo Ativo 31/12\n"
        "2025;212405;2304400;CE;SIM\n"
        "2024;xx;;Ceará;talvez\n",
        encoding="utf-8",
    )
    layout, semantic, values = _prepare_reports(tmp_path)
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        'families:\n  "2122": "Engenheiros em computação"\n',
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
    assert result.rows_unknown_status_source == 0
    assert result.rows_year_mismatch_source == 1
    rejected = pq.read_table(result.reject_path).to_pylist()
    assert len(rejected) == 1
    assert "invalid_year" in rejected[0]["reason"]
    assert "invalid_active_status" in rejected[0]["reason"]
    assert "invalid_cbo" in rejected[0]["reason"]
    assert "missing_municipality" in rejected[0]["reason"]
    assert "invalid_uf" in rejected[0]["reason"]

    quality = json.loads(result.quality_path.read_text(encoding="utf-8"))
    assert quality["source_partition_complete"] is True
    assert quality["gold_ready"] is False
    assert quality["publication_ready"] is False


def test_transform_rais_year_requires_value_semantics_ready(tmp_path: Path):
    layout, semantic, values = _prepare_reports(tmp_path)
    payload = json.loads(values.read_text(encoding="utf-8"))
    payload["silver_transform_ready"] = False
    values.write_text(json.dumps(payload), encoding="utf-8")

    cbo = tmp_path / "cbo.yml"
    cbo.write_text('families:\n  "2122": "Tech"\n', encoding="utf-8")

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
