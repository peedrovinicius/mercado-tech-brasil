import json
from pathlib import Path

import pytest

from src.transform.rais_profile import profile_rais_values


def _write_reports(base: Path, *, silver_ready: bool = True) -> tuple[Path, Path]:
    layout = base / "layout-report.json"
    semantic = base / "semantic-layout-report.json"

    layout.write_text(
        json.dumps(
            {
                "year": 2025,
                "files": [
                    {
                        "file": "RAIS_VINC_TESTE.comt",
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
                "contract_version": 3,
                "silver_ready": silver_ready,
                "files": [
                    {
                        "file": "RAIS_VINC_TESTE.comt",
                        "valid": silver_ready,
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
    return layout, semantic


def test_profile_rais_values_reports_stock_codes(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    source = extracted / "RAIS_VINC_TESTE.comt"
    source.write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código,Ind Vínculo Abandonado - Código\n"
        "212405,2304400,1,0\n"
        "317110,3550308,1,1\n"
        "212405,2304400,0,0\n",
        encoding="utf-8",
    )
    layout, semantic = _write_reports(tmp_path)
    destination = tmp_path / "value-profile.json"

    payload = profile_rais_values(
        extracted,
        layout,
        semantic,
        destination,
        max_rows_per_file=100,
    )

    assert payload["profile_complete"] is True
    assert payload["aggregate"]["active_3112"]["observed_values"] == ["0", "1"]
    assert payload["aggregate"]["abandoned_link"]["observed_values"] == ["0", "1"]
    assert payload["aggregate"]["abandoned_link"]["top_values"] == [
        {"value": "0", "count": 2},
        {"value": "1", "count": 1},
    ]
    assert payload["aggregate"]["year"]["observed_values"] == ["2025"]


def test_profile_requires_semantic_validation(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    layout, semantic = _write_reports(tmp_path, silver_ready=False)

    with pytest.raises(ValueError, match="silver_ready=true"):
        profile_rais_values(
            extracted,
            layout,
            semantic,
            tmp_path / "profile.json",
        )


def test_profile_rejects_excessive_sample_limit(tmp_path: Path):
    with pytest.raises(ValueError, match="entre 1 e 100000"):
        profile_rais_values(
            tmp_path,
            tmp_path / "layout.json",
            tmp_path / "semantic.json",
            tmp_path / "profile.json",
            max_rows_per_file=100001,
        )
