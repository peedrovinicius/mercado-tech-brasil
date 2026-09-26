import polars as pl
import pytest

from src.methodology.salary import add_salary_eligibility, methodology_for_competence


def test_2026_salary_bounds_follow_mte_rule():
    methodology = methodology_for_competence("202607")
    assert methodology.minimum_wage_brl == 1621.00
    assert methodology.minimum_salary_brl == 486.30
    assert methodology.maximum_salary_brl == 243150.00


def test_salary_eligibility_excludes_outliers_and_intermittent():
    frame = pl.DataFrame(
        {
            "saldo_movimentacao": [1, 1, 1, 1, -1],
            "salario_mensal": [486.30, 243150.00, 400.00, 5000.00, 9000.00],
            "indicador_trabalho_intermitente": ["0", "0", "0", "1", "0"],
        }
    )
    result = add_salary_eligibility(frame, yearmonth="202607")
    assert result["salario_admissao_elegivel"].to_list() == [
        True,
        True,
        False,
        False,
        False,
    ]


def test_salary_methodology_fails_without_intermittent_indicator():
    frame = pl.DataFrame(
        {
            "saldo_movimentacao": [1],
            "salario_mensal": [5000.00],
        }
    )
    with pytest.raises(ValueError, match="indicador_trabalho_intermitente"):
        add_salary_eligibility(frame, yearmonth="202607")
