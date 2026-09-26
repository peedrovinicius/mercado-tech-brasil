import json
from pathlib import Path

from src.transform.rais_semantics import validate_layout_semantics


CONTRACT = """version: 1
dataset: rais_vinculos
required:
  year:
    aliases: [ano, ano_base]
  cbo_occupation:
    aliases: [cbo_ocupacao_2002, cbo]
  municipality:
    aliases: [municipio, mun_trab]
  uf:
    aliases: [uf, uf_trabalho]
  active_3112:
    aliases: [vinculo_ativo_31_12, emp_em_31_12]
optional:
  remuneration:
    aliases: [vl_remun_dezembro_nom]
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
            "ano",
            "cbo_ocupacao_2002",
            "municipio",
            "uf",
            "vinculo_ativo_31_12",
            "vl_remun_dezembro_nom",
        ],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_layout_semantics(layout, contract, destination)

    assert payload["semantic_valid"] is True
    assert payload["silver_ready"] is True
    assert payload["publication_ready"] is False
    assert payload["files"][0]["missing_required"] == []


def test_semantic_contract_blocks_missing_required_concept(tmp_path: Path):
    layout = tmp_path / "layout.json"
    contract = tmp_path / "contract.yml"
    destination = tmp_path / "semantic.json"

    _write_layout(
        layout,
        [
            "ano",
            "cbo_ocupacao_2002",
            "municipio",
            "uf",
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
            "ano",
            "cbo_ocupacao_2002",
            "cbo",
            "municipio",
            "uf",
            "vinculo_ativo_31_12",
        ],
    )
    contract.write_text(CONTRACT, encoding="utf-8")

    payload = validate_layout_semantics(layout, contract, destination)

    assert payload["semantic_valid"] is False
    assert payload["silver_ready"] is False
    assert payload["files"][0]["ambiguous_required"] == ["cbo_occupation"]
