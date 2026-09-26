import json
from pathlib import Path

from src.transform.rais_semantics import validate_layout_semantics


CONTRACT = """version: 2
dataset: rais_vinculos
required:
  cbo_occupation:
    aliases: [cbo_2002_ocupacao_codigo, cbo]
  municipality:
    aliases: [municipio_codigo, municipio]
  active_3112:
    aliases: [ind_vinculo_ativo_31_12_codigo, vinculo_ativo_31_12]
derived:
  year:
    strategy: annual_context
  uf:
    strategy: municipality_code
optional:
  remuneration:
    aliases: [vl_rem_dezembro_nom]
"""


def _write_layout(path: Path, columns: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "year": 2025,
                "files": [
                    {
                        "file": "RAIS_VINC_TESTE.comt",
                        "header_signature_sha256": "abc123",
                        "normalized_columns": columns,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_semantic_contract_marks_silver_ready_when_required_concepts_match(
    tmp_path: Path,
):
    layout = tmp_path / "layout.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "semantic.json"

    _write_layout(
        layout,
        [
            "cbo_2002_ocupacao_codigo",
            "municipio_codigo",
            "ind_vinculo_ativo_31_12_codigo",
            "vl_rem_dezembro_nom",
        ],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_layout_semantics(layout, contract, destination)

    assert payload["semantic_valid"] is True
    assert payload["silver_ready"] is True
    assert payload["publication_ready"] is False
    assert payload["files"][0]["missing_required"] == []
    assert payload["derived"]["year"]["strategy"] == "annual_context"
    assert payload["derived"]["uf"]["strategy"] == "municipality_code"


def test_semantic_contract_blocks_missing_required_concept(tmp_path: Path):
    layout = tmp_path / "layout.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "semantic.json"

    _write_layout(
        layout,
        [
            "cbo_2002_ocupacao_codigo",
            "municipio_codigo",
        ],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_layout_semantics(layout, contract, destination)

    assert payload["semantic_valid"] is False
    assert payload["silver_ready"] is False
    assert payload["files"][0]["missing_required"] == ["active_3112"]


def test_semantic_contract_blocks_ambiguous_aliases(tmp_path: Path):
    layout = tmp_path / "layout.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "semantic.json"

    _write_layout(
        layout,
        [
            "cbo_2002_ocupacao_codigo",
            "cbo",
            "municipio_codigo",
            "ind_vinculo_ativo_31_12_codigo",
        ],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_layout_semantics(layout, contract, destination)

    assert payload["semantic_valid"] is False
    assert payload["silver_ready"] is False
    assert payload["files"][0]["ambiguous_required"] == ["cbo_occupation"]
