import json
from pathlib import Path

from src.reference.population import save_population_cache
from src.validation.population_enrichment import (
    enrich_published_municipality_population,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _population_fixture(path: Path) -> None:
    populations = {
        f"{1000000 + index:07d}": 1000 + index
        for index in range(5000)
    }
    populations["2304400"] = 2700000
    populations["3550308"] = 12000000
    save_population_cache(
        populations,
        year=2026,
        destination=path,
    )


def test_enrich_published_municipality_population_preserves_totals(
    tmp_path: Path,
):
    gold = tmp_path / "gold"
    population = tmp_path / "population.json"
    _population_fixture(population)

    _write_json(
        gold / "publication-gate-202607.json",
        {
            "competence": "202607",
            "publishable": True,
        },
    )
    _write_json(
        gold / "by-municipality-202607.json",
        {
            "competence": "202607",
            "source": "Novo CAGED / MTE",
            "items": [
                {
                    "municipio_codigo_caged": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "admissions": 270,
                    "dismissals": 135,
                    "balance": 135,
                },
                {
                    "municipio_codigo_caged": "355030",
                    "municipio_codigo_ibge": "3550308",
                    "municipio_nome": "São Paulo",
                    "uf": "SP",
                    "admissions": 1200,
                    "dismissals": 960,
                    "balance": 240,
                },
                {
                    "municipio_codigo_caged": "999999",
                    "municipio_codigo_ibge": None,
                    "municipio_nome": "Não identificado",
                    "uf": "NI",
                    "admissions": 3,
                    "dismissals": 1,
                    "balance": 2,
                },
            ],
        },
    )

    report = enrich_published_municipality_population(
        yearmonth="202607",
        population_year=2026,
        gold_dir=gold,
        population_cache_path=population,
        source_url="https://www.ibge.gov.br/estimativas",
        published_at="2026-08-28",
    )

    assert report["coverage_complete"] is True
    assert report["identified_municipalities"] == 2
    assert report["residual_municipalities"] == 1
    assert report["missing_population"] == 0
    assert report["totals_before"] == report["totals_after"]

    payload = json.loads(
        (gold / "by-municipality-202607.json").read_text(encoding="utf-8")
    )
    assert payload["population_reference_year"] == 2026
    assert payload["population_reference_date"] == "2026-07-01"
    assert payload["population_enrichment_status"] == "complete"

    by_code = {
        item["municipio_codigo_caged"]: item
        for item in payload["items"]
    }
    assert by_code["230440"]["population_estimate"] == 2700000
    assert by_code["230440"]["admissions_per_100k"] == 10.0
    assert by_code["355030"]["admissions_per_100k"] == 10.0
    assert by_code["999999"]["population_estimate"] is None
    assert by_code["999999"]["admissions_per_100k"] is None


def test_enrichment_blocks_missing_population(tmp_path: Path):
    gold = tmp_path / "gold"
    population = tmp_path / "population.json"
    _population_fixture(population)

    _write_json(
        gold / "publication-gate-202607.json",
        {
            "competence": "202607",
            "publishable": True,
        },
    )
    _write_json(
        gold / "by-municipality-202607.json",
        {
            "competence": "202607",
            "items": [
                {
                    "municipio_codigo_caged": "000001",
                    "municipio_codigo_ibge": "9999999",
                    "municipio_nome": "Teste",
                    "uf": "TS",
                    "admissions": 1,
                    "dismissals": 0,
                    "balance": 1,
                }
            ],
        },
    )

    try:
        enrich_published_municipality_population(
            yearmonth="202607",
            population_year=2026,
            gold_dir=gold,
            population_cache_path=population,
            source_url="https://www.ibge.gov.br/estimativas",
            published_at="2026-08-28",
        )
    except ValueError as exc:
        assert "Cobertura populacional incompleta" in str(exc)
    else:
        raise AssertionError("Expected missing population to block enrichment")


def test_enrichment_is_idempotent_for_same_population_reference(
    tmp_path: Path,
):
    gold = tmp_path / "gold"
    population = tmp_path / "population.json"
    _population_fixture(population)

    _write_json(
        gold / "publication-gate-202607.json",
        {
            "competence": "202607",
            "publishable": True,
        },
    )
    _write_json(
        gold / "by-municipality-202607.json",
        {
            "competence": "202607",
            "items": [
                {
                    "municipio_codigo_caged": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "admissions": 270,
                    "dismissals": 135,
                    "balance": 135,
                }
            ],
        },
    )

    first = enrich_published_municipality_population(
        yearmonth="202607",
        population_year=2026,
        gold_dir=gold,
        population_cache_path=population,
        source_url="https://www.ibge.gov.br/estimativas",
        published_at="2026-08-28",
    )
    municipality_path = gold / "by-municipality-202607.json"
    report_path = gold / "population-enrichment-202607.json"
    municipality_after_first = municipality_path.read_bytes()
    report_after_first = report_path.read_bytes()

    second = enrich_published_municipality_population(
        yearmonth="202607",
        population_year=2026,
        gold_dir=gold,
        population_cache_path=population,
        source_url="https://www.ibge.gov.br/estimativas",
        published_at="2026-08-28",
    )

    assert first["_changed"] is True
    assert second["_changed"] is False
    assert municipality_path.read_bytes() == municipality_after_first
    assert report_path.read_bytes() == report_after_first
    assert "_changed" not in json.loads(
        report_path.read_text(encoding="utf-8")
    )
    assert (
        second["municipality_artifact_before_sha256"]
        == first["municipality_artifact_before_sha256"]
    )


def test_prepublication_candidate_allows_population_only_failures(
    tmp_path: Path,
):
    gold = tmp_path / "gold"
    population = tmp_path / "population.json"
    _population_fixture(population)

    _write_json(
        gold / "publication-gate-202608.json",
        {
            "competence": "202608",
            "publishable": False,
            "checks": [
                {
                    "id": "quality_report",
                    "passed": True,
                    "blocking": True,
                },
                {
                    "id": "municipality_population_metadata",
                    "passed": False,
                    "blocking": True,
                },
                {
                    "id": "municipality_population_report",
                    "passed": False,
                    "blocking": True,
                },
                {
                    "id": "manual_methodology_approval",
                    "passed": False,
                    "blocking": True,
                },
            ],
        },
    )
    _write_json(
        gold / "by-municipality-202608.json",
        {
            "competence": "202608",
            "source": "Novo CAGED / MTE",
            "items": [
                {
                    "municipio_codigo_caged": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "admissions": 270,
                    "dismissals": 135,
                    "balance": 135,
                }
            ],
        },
    )

    report = enrich_published_municipality_population(
        yearmonth="202608",
        population_year=2026,
        gold_dir=gold,
        population_cache_path=population,
        source_url="https://www.ibge.gov.br/estimativas",
        published_at="2026-08-28",
        allow_unpublished_candidate=True,
    )

    assert report["coverage_complete"] is True
    assert report["matched_population"] == 1
    payload = json.loads(
        (gold / "by-municipality-202608.json").read_text(encoding="utf-8")
    )
    assert payload["population_enrichment_status"] == "complete"


def test_prepublication_candidate_rejects_other_blocking_failures(
    tmp_path: Path,
):
    gold = tmp_path / "gold"
    population = tmp_path / "population.json"
    _population_fixture(population)

    _write_json(
        gold / "publication-gate-202608.json",
        {
            "competence": "202608",
            "publishable": False,
            "checks": [
                {
                    "id": "national_reference_reconciliation",
                    "passed": False,
                    "blocking": True,
                },
                {
                    "id": "municipality_population_metadata",
                    "passed": False,
                    "blocking": True,
                },
                {
                    "id": "municipality_population_report",
                    "passed": False,
                    "blocking": True,
                },
                {
                    "id": "manual_methodology_approval",
                    "passed": False,
                    "blocking": True,
                },
            ],
        },
    )
    _write_json(
        gold / "by-municipality-202608.json",
        {
            "competence": "202608",
            "items": [
                {
                    "municipio_codigo_caged": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "admissions": 1,
                    "dismissals": 0,
                    "balance": 1,
                }
            ],
        },
    )

    try:
        enrich_published_municipality_population(
            yearmonth="202608",
            population_year=2026,
            gold_dir=gold,
            population_cache_path=population,
            source_url="https://www.ibge.gov.br/estimativas",
            published_at="2026-08-28",
            allow_unpublished_candidate=True,
        )
    except ValueError as exc:
        assert "falhas bloqueantes anteriores" in str(exc)
        assert "national_reference_reconciliation" in str(exc)
    else:
        raise AssertionError("Expected blocking gate failure to reject enrichment")
