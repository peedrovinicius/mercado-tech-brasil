import polars as pl

from src.transform.adjustments import (
    _effective_competence_expr,
    add_adjustment_deltas,
)


def test_for_adds_original_movement_effect():
    frame = pl.DataFrame({"saldo_movimentacao": [1, -1]})
    result = add_adjustment_deltas(frame, kind="FOR")

    assert result["admissions_delta"].to_list() == [1, 0]
    assert result["dismissals_delta"].to_list() == [0, 1]
    assert result["balance_delta"].to_list() == [1, -1]


def test_exc_inverts_original_movement_effect():
    frame = pl.DataFrame({"saldo_movimentacao": [1, -1]})
    result = add_adjustment_deltas(frame, kind="EXC")

    assert result["admissions_delta"].to_list() == [-1, 0]
    assert result["dismissals_delta"].to_list() == [0, -1]
    assert result["balance_delta"].to_list() == [-1, 1]


def test_adjustment_prefers_movement_competence():
    frame = pl.DataFrame(
        {
            "competencia_mov": ["202607"],
            "competencia_declarada": ["202608"],
        }
    )
    result = frame.with_columns(
        _effective_competence_expr(frame, "FOR", "202609")
    )

    assert result["effective_competence"].to_list() == ["202607"]


def test_adjustment_uses_ingest_competence_when_fields_are_blank():
    frame = pl.DataFrame(
        {
            "competencia_mov": [""],
            "competencia_declarada": [""],
        }
    )
    result = frame.with_columns(
        _effective_competence_expr(frame, "EXC", "202609")
    )

    assert result["effective_competence"].to_list() == ["202609"]
