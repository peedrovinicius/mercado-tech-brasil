from src.transform.schema import (
    UF_CODE_TO_SIGLA,
    normalize_column_name,
    validate_core_columns,
)


def test_normalizes_official_headers():
    assert normalize_column_name("CBO 2002 Ocupação") == "cbo2002ocupacao"
    assert normalize_column_name("saldo movimentação") == "saldomovimentacao"
    assert normalize_column_name("salário") == "salario"


def test_expected_layout_passes():
    normalized = {
        "competenciamov",
        "uf",
        "municipio",
        "saldomovimentacao",
        "cbo2002ocupacao",
        "tipomovimentacao",
        "salario",
    }
    assert validate_core_columns(normalized) == set()


def test_layout_change_is_detected():
    normalized = {"uf", "municipio"}
    missing = validate_core_columns(normalized)
    assert "cbo2002ocupacao" in missing
    assert "saldomovimentacao" in missing


def test_non_identified_uf_is_valid_category():
    assert UF_CODE_TO_SIGLA["99"] == "NI"
