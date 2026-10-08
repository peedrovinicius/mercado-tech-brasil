import csv
import io

from src.api.routers.export import _csv_bytes


def test_csv_export_neutralizes_spreadsheet_formulas():
    rows = [
        {"name": "=SUM(1,1)", "note": "  @unsafe", "admissions": 42, "balance": -5},
        {"name": "+CMD", "note": "-injected", "admissions": 0, "balance": 3},
    ]

    payload = _csv_bytes(rows).decode("utf-8-sig")
    parsed = list(csv.DictReader(io.StringIO(payload)))

    assert parsed[0]["name"] == "'=SUM(1,1)"
    assert parsed[0]["note"] == "'  @unsafe"
    assert parsed[1]["name"] == "'+CMD"
    assert parsed[1]["note"] == "'-injected"
    assert parsed[0]["admissions"] == "42"
    assert parsed[0]["balance"] == "-5"


def test_csv_export_preserves_safe_text_and_empty_export():
    assert _csv_bytes([]) == b""
    result = list(csv.DictReader(io.StringIO(_csv_bytes([{"name": "Ceará"}]).decode("utf-8-sig"))))
    assert result == [{"name": "Ceará"}]
