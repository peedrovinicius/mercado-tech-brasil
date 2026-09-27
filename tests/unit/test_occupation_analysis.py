import json
from pathlib import Path

from src.api.occupation_analysis import build_occupation_family_trend


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_occupation_family_trend_aggregates_codes_by_family(tmp_path: Path):
    gold = tmp_path / "gold"
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        (
            "families:\n"
            "  \"2124\": \"Analistas de tecnologia da informação\"\n"
            "  \"3171\": \"Técnicos de desenvolvimento de sistemas e aplicações\"\n"
        ),
        encoding="utf-8",
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
                    "dismissals": 7,
                    "balance": 3,
                },
                {
                    "cbo_familia": "2124",
                    "cbo_codigo": "212410",
                    "admissions": 5,
                    "dismissals": 6,
                    "balance": -1,
                },
                {
                    "cbo_familia": "3171",
                    "cbo_codigo": "317110",
                    "admissions": 4,
                    "dismissals": 3,
                    "balance": 1,
                },
            ],
        },
    )
    _write_json(
        gold / "by-occupation-202602.json",
        {
            "competence": "202602",
            "items": [
                {
                    "cbo_familia": "2124",
                    "cbo_codigo": "212405",
                    "admissions": 8,
                    "dismissals": 9,
                    "balance": -1,
                },
                {
                    "cbo_familia": "3171",
                    "cbo_codigo": "317110",
                    "admissions": 6,
                    "dismissals": 4,
                    "balance": 2,
                },
            ],
        },
    )

    result = build_occupation_family_trend(
        gold_dir=gold,
        cbo_config_path=cbo,
        competencies=["202602", "202601"],
    )

    assert result["published_from"] == "202601"
    assert result["published_to"] == "202602"
    assert result["published_months"] == 2

    families = {
        item["cbo_familia"]: item
        for item in result["families"]
    }
    assert families["2124"]["admissions"] == 23
    assert families["2124"]["dismissals"] == 22
    assert families["2124"]["balance"] == 1
    assert families["2124"]["monthly"] == [
        {
            "competence": "202601",
            "admissions": 15,
            "dismissals": 13,
            "balance": 2,
        },
        {
            "competence": "202602",
            "admissions": 8,
            "dismissals": 9,
            "balance": -1,
        },
    ]
    assert families["3171"]["admissions"] == 10
    assert families["3171"]["balance"] == 3
    assert round(families["2124"]["share_of_tech_admissions"], 6) == round(
        23 / 33,
        6,
    )
