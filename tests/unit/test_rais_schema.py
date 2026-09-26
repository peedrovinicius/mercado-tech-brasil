import json
from pathlib import Path

import pytest

from src.transform.rais_schema import (
    detect_delimiter,
    inspect_rais_directory,
    inspect_rais_file,
    normalize_column_name,
)


def test_normalize_rais_column_name():
    assert normalize_column_name("CBO Ocupação 2002") == "cbo_ocupacao_2002"
    assert normalize_column_name("Município") == "municipio"
    assert normalize_column_name("Vl Remun Média (SM)") == "vl_remun_media_sm"


def test_detect_semicolon_delimiter():
    assert detect_delimiter("A;B;C;D;E") == ";"


def test_inspect_comt_layout(tmp_path: Path):
    source = tmp_path / "RAIS_VINC_PUB_TESTE.comt"
    source.write_text(
        "Ano;CBO Ocupação 2002;Município;UF;Vínculo Ativo 31/12\n"
        "2025;212405;2304400;CE;1\n",
        encoding="utf-8",
    )

    result = inspect_rais_file(source)

    assert result.suffix == ".comt"
    assert result.encoding in {"utf-8-sig", "utf-8"}
    assert result.delimiter == ";"
    assert result.column_count == 5
    assert result.normalized_columns == [
        "ano",
        "cbo_ocupacao_2002",
        "municipio",
        "uf",
        "vinculo_ativo_31_12",
    ]
    assert len(result.header_signature_sha256) == 64


def test_inspect_latin1_txt_layout(tmp_path: Path):
    source = tmp_path / "rais.txt"
    source.write_bytes(
        (
            "Ano;Ocupação;Município;UF;Remuneração\n"
            "2025;212405;2304400;CE;5000\n"
        ).encode("latin-1")
    )

    result = inspect_rais_file(source)

    assert result.encoding == "latin-1"
    assert result.normalized_columns[1] == "ocupacao"


def test_directory_report_keeps_publication_blocked(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "a.comt").write_text(
        "A;B;C;D;E\n1;2;3;4;5\n",
        encoding="utf-8",
    )
    (extracted / "b.txt").write_text(
        "A;B;C;D;E\n6;7;8;9;10\n",
        encoding="utf-8",
    )
    destination = tmp_path / "layout-report.json"

    payload = inspect_rais_directory(
        extracted,
        year=2025,
        destination=destination,
    )

    assert payload["files_inspected"] == 2
    assert payload["unique_layouts"] == 1
    assert payload["silver_ready"] is False
    assert payload["publication_ready"] is False

    stored = json.loads(destination.read_text(encoding="utf-8"))
    assert stored["year"] == 2025


def test_rejects_unsupported_extension(tmp_path: Path):
    source = tmp_path / "arquivo.xlsx"
    source.write_text("A;B;C;D;E", encoding="utf-8")

    with pytest.raises(ValueError):
        inspect_rais_file(source)
