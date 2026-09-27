import json
from pathlib import Path

from openpyxl import Workbook

from src.reference.qbq import (
    inspect_qbq_workbook,
    normalize_cbo_code,
    validate_qbq_workbook,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _workbook(path: Path, codes: list[object]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Ocupacoes"
    sheet.append(["Codigo CBO", "Titulo", "Nivel"])
    for index, code in enumerate(codes, start=1):
        sheet.append([code, f"Ocupacao {index}", 5])
    workbook.save(path)
    workbook.close()


def test_normalize_cbo_code_accepts_excel_variants():
    assert normalize_cbo_code(212405) == "212405"
    assert normalize_cbo_code(212405.0) == "212405"
    assert normalize_cbo_code("2124-05") == "212405"
    assert normalize_cbo_code(" 317110 ") == "317110"
    assert normalize_cbo_code(True) is None
    assert normalize_cbo_code("2124") is None


def test_inspect_qbq_workbook_detects_cbo_join_and_fingerprint(tmp_path: Path):
    source = tmp_path / "qbq.xlsx"
    _workbook(source, [212405, "3171-10", 999999])

    result = inspect_qbq_workbook(
        source,
        expected_codes={"212405", "317110"},
    )

    assert result["coverage_complete"] is True
    assert result["matched_tech_codes"] == ["212405", "317110"]
    assert result["missing_tech_codes"] == []
    assert len(result["source_sha256"]) == 64
    assert result["source_size_bytes"] > 0
    assert result["detected_join_columns"] == [
        {
            "sheet": "Ocupacoes",
            "column_index": 1,
            "header": "Codigo CBO",
            "matched_codes": ["212405", "317110"],
            "matched_count": 2,
        }
    ]


def test_inspect_qbq_workbook_reports_missing_tech_codes(tmp_path: Path):
    source = tmp_path / "qbq.xlsx"
    _workbook(source, [212405])

    result = inspect_qbq_workbook(
        source,
        expected_codes={"212405", "317110"},
    )

    assert result["coverage_complete"] is False
    assert result["missing_tech_codes"] == ["317110"]


def test_validate_qbq_workbook_uses_only_published_occupation_codes(
    tmp_path: Path,
):
    gold = tmp_path / "gold"
    _write_json(
        gold / "publication-gate-202601.json",
        {
            "competence": "202601",
            "automatic_checks_passed": True,
            "manual_approval_valid": True,
            "publishable": True,
        },
    )
    _write_json(
        gold / "by-occupation-202601.json",
        {
            "competence": "202601",
            "items": [
                {
                    "cbo_familia": "2124",
                    "cbo_codigo": "212405",
                    "admissions": 10,
                    "dismissals": 8,
                    "balance": 2,
                },
                {
                    "cbo_familia": "3171",
                    "cbo_codigo": "317110",
                    "admissions": 5,
                    "dismissals": 4,
                    "balance": 1,
                },
            ],
        },
    )

    source = tmp_path / "qbq.xlsx"
    _workbook(source, [212405, 317110, 123456])

    result = validate_qbq_workbook(
        source,
        gold_dir=gold,
    )

    assert result["expected_tech_codes"] == ["212405", "317110"]
    assert result["coverage_complete"] is True
