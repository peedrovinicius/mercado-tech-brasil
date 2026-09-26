from __future__ import annotations

from dataclasses import dataclass


MINIMUM_WAGE_BY_YEAR = {
    2026: 1621.00,
}


@dataclass(frozen=True)
class SalaryMethodology:
    year: int
    minimum_wage_brl: float
    minimum_multiple: float
    maximum_multiple: float
    minimum_salary_brl: float
    maximum_salary_brl: float


def methodology_for_competence(yearmonth: str) -> SalaryMethodology:
    if len(yearmonth) != 6 or not yearmonth.isdigit():
        raise ValueError("Competência deve estar no formato AAAAMM.")

    year = int(yearmonth[:4])
    minimum_wage = MINIMUM_WAGE_BY_YEAR.get(year)
    if minimum_wage is None:
        raise ValueError(
            f"Salário mínimo não configurado para {year}; "
            "não é seguro calcular a metodologia salarial."
        )

    minimum_multiple = 0.3
    maximum_multiple = 150.0
    return SalaryMethodology(
        year=year,
        minimum_wage_brl=minimum_wage,
        minimum_multiple=minimum_multiple,
        maximum_multiple=maximum_multiple,
        minimum_salary_brl=round(minimum_wage * minimum_multiple, 2),
        maximum_salary_brl=round(minimum_wage * maximum_multiple, 2),
    )


def add_salary_eligibility(frame, *, yearmonth: str):
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError(
            "Polars não está instalado. Execute pip install -e ."
        ) from exc

    required = {
        "saldo_movimentacao",
        "salario_mensal",
        "indicador_trabalho_intermitente",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            "Não é possível reproduzir a metodologia salarial do MTE. "
            "Colunas ausentes: " + ", ".join(sorted(missing))
        )

    methodology = methodology_for_competence(yearmonth)
    intermittent = (
        pl.col("indicador_trabalho_intermitente")
        .cast(pl.Utf8, strict=False)
        .str.strip_chars()
        .str.to_lowercase()
        .is_in(["1", "1.0", "true", "sim", "s"])
    )

    eligible = (
        (pl.col("saldo_movimentacao") == 1)
        & pl.col("salario_mensal").is_not_null()
        & (pl.col("salario_mensal") >= methodology.minimum_salary_brl)
        & (pl.col("salario_mensal") <= methodology.maximum_salary_brl)
        & (~intermittent)
    )

    return frame.with_columns(
        eligible.alias("salario_admissao_elegivel"),
    )
