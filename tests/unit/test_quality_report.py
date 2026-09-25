import pytest

from src.quality.report import make_report


def test_quality_report_valid_rate():
    report = make_report(
        source="novo_caged",
        competence="2026-07",
        rows_read=100,
        rows_valid=97,
        rejection_reasons={"invalid_cbo": 2, "invalid_uf": 1},
    )
    assert report.rows_rejected == 3
    assert report.valid_rate == 0.97


def test_quality_report_rejects_inconsistent_counts():
    with pytest.raises(ValueError):
        make_report(
            source="novo_caged",
            competence="2026-07",
            rows_read=10,
            rows_valid=9,
            rejection_reasons={"invalid": 2},
        )
