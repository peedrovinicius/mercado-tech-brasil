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
                "contract_version": 2,
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
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return layout, semantic


def test_profile_rais_values_reports_observed_codes(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    source = extracted / "RAIS_VINC_TESTE.comt"
    source.write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código\n"
        "212405,2304400,1\n"
        "317110,3550308,1\n"
        "212405,2304400,0\n",
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

    assert payload["files_profiled"] == 1
    assert payload["profile_complete"] is True
    assert payload["silver_transform_ready"] is False
    assert payload["publication_ready"] is False

    active = payload["aggregate"]["active_3112"]
    assert active["top_values"] == [
        {"value": "1", "count": 2},
        {"value": "0", "count": 1},
    ]

    year = payload["aggregate"]["year"]
    assert year["derived"] is True
    assert year["observed_values"] == ["2025"]
    assert year["top_values"] == [{"value": "2025", "count": 3}]

    cbo = payload["aggregate"]["cbo_occupation"]
    assert cbo["digits_only"] == 3
    assert cbo["lengths"] == {"6": 3}


def test_profile_requires_semantic_validation(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "RAIS_VINC_TESTE.comt").write_text(
        "CBO 2002 Ocupação - Código,Município - Código,"
        "Ind Vínculo Ativo 31/12 - Código\n"
        "212405,2304400,1\n",
        encoding="utf-8",
    )
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
