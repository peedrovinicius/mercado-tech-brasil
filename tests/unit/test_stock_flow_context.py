import json
from pathlib import Path

from src.api.stock_flow_context import build_stock_flow_context


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_stock_flow_context_aligns_same_cbo_families(tmp_path: Path):
    gold = tmp_path / "gold"
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        (
            "families:\n"
            "  \"2124\": \"Analistas de tecnologia da informação\"\n"
            "  \"3172\": \"Técnicos em operação e monitoração de computadores\"\n"
        ),
        encoding="utf-8",
    )

    _write_json(
        gold / "rais-publication-gate-2025.json",
        {
            "year": 2025,
            "publishable": True,
        },
    )
    _write_json(
        gold / "rais-by-cbo-family-2025.json",
        {
            "year": 2025,
            "reference_date": "2025-12-31",
            "source": "RAIS / MTE",
            "items": [
                {
                    "cbo_familia": "2124",
                    "cbo_familia_nome": "Analistas de tecnologia da informação",
                    "active_stock": 100,
                    "share_of_tech_stock": 2 / 3,
                },
                {
                    "cbo_familia": "3172",
                    "cbo_familia_nome": "Técnicos em operação e monitoração de computadores",
                    "active_stock": 50,
                    "share_of_tech_stock": 1 / 3,
                },
            ],
        },
    )

    for competence, items in {
        "202601": [
            {
                "cbo_familia": "2124",
                "cbo_codigo": "212405",
                "admissions": 10,
                "dismissals": 8,
                "balance": 2,
            },
            {
                "cbo_familia": "3172",
                "cbo_codigo": "317210",
                "admissions": 8,
                "dismissals": 5,
                "balance": 3,
            },
        ],
        "202602": [
            {
                "cbo_familia": "2124",
                "cbo_codigo": "212405",
                "admissions": 5,
                "dismissals": 6,
                "balance": -1,
            },
            {
                "cbo_familia": "3172",
                "cbo_codigo": "317210",
                "admissions": 7,
                "dismissals": 5,
                "balance": 2,
            },
        ],
    }.items():
        _write_json(
            gold / f"publication-gate-{competence}.json",
            {
                "competence": competence,
                "publishable": True,
            },
        )
        _write_json(
            gold / f"by-occupation-{competence}.json",
            {
                "competence": competence,
                "items": items,
            },
        )

    result = build_stock_flow_context(
        gold_dir=gold,
        cbo_config_path=cbo,
    )

    assert result["rais_year"] == 2025
    assert result["stock_reference_date"] == "2025-12-31"
    assert result["caged_from"] == "202601"
    assert result["caged_to"] == "202602"
    assert result["published_months"] == 2
    assert result["totals"] == {
        "active_stock": 150,
        "admissions": 30,
        "dismissals": 24,
        "balance": 6,
        "admissions_per_100_prior_stock": 20.0,
        "dismissals_per_100_prior_stock": 16.0,
        "balance_per_100_prior_stock": 4.0,
    }

    families = {
        item["cbo_familia"]: item
        for item in result["families"]
    }
    assert families["2124"]["active_stock"] == 100
    assert families["2124"]["admissions"] == 15
    assert families["2124"]["balance"] == 1
    assert families["2124"]["admissions_per_100_prior_stock"] == 15.0
    assert round(families["2124"]["composition_gap_pp"], 6) == round(
        (15 / 30 - 100 / 150) * 100,
        6,
    )
    assert families["3172"]["admissions_per_100_prior_stock"] == 30.0


def test_stock_flow_context_rejects_family_mismatch(tmp_path: Path):
    gold = tmp_path / "gold"
    cbo = tmp_path / "cbo.yml"
    cbo.write_text(
        (
            "families:\n"
            "  \"2124\": \"Analistas de tecnologia da informação\"\n"
            "  \"3172\": \"Técnicos em operação e monitoração de computadores\"\n"
        ),
        encoding="utf-8",
    )

    _write_json(
        gold / "rais-publication-gate-2025.json",
        {"year": 2025, "publishable": True},
    )
    _write_json(
        gold / "rais-by-cbo-family-2025.json",
        {
            "year": 2025,
            "items": [
                {
                    "cbo_familia": "2124",
                    "active_stock": 100,
                }
            ],
        },
    )
    _write_json(
        gold / "publication-gate-202601.json",
        {"competence": "202601", "publishable": True},
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
                    "cbo_familia": "3172",
                    "cbo_codigo": "317210",
                    "admissions": 5,
                    "dismissals": 4,
                    "balance": 1,
                },
            ],
        },
    )

    try:
        build_stock_flow_context(
            gold_dir=gold,
            cbo_config_path=cbo,
        )
    except ValueError as exc:
        assert "Famílias CBO divergentes" in str(exc)
    else:
        raise AssertionError("Expected family mismatch to be rejected")
