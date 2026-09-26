import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import src.api.routers.analytics as analytics_router
from src.api.main import app

client = TestClient(app)


def test_normalized_municipality_ranking_uses_rate_and_excludes_missing_denominator(
    monkeypatch,
    tmp_path: Path,
):
    payload_path = tmp_path / "by-municipality-202607.json"
    payload_path.write_text(
        json.dumps(
            {
                "competence": "202607",
                "source": "Novo CAGED / MTE",
                "population_source": "IBGE SIDRA",
                "population_reference_year": 2026,
                "population_reference_date": "2026-07-01",
                "items": [
                    {
                        "municipio_codigo_caged": "111111",
                        "municipio_nome": "Município A",
                        "uf": "AA",
                        "admissions": 500,
                        "dismissals": 400,
                        "balance": 100,
                        "admissions_per_100k": 4.0,
                    },
                    {
                        "municipio_codigo_caged": "222222",
                        "municipio_nome": "Município B",
                        "uf": "BB",
                        "admissions": 100,
                        "dismissals": 60,
                        "balance": 40,
                        "admissions_per_100k": 12.0,
                    },
                    {
                        "municipio_codigo_caged": "999999",
                        "municipio_nome": "Não identificado",
                        "uf": "NI",
                        "admissions": 900,
                        "dismissals": 800,
                        "balance": 100,
                        "admissions_per_100k": None,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        analytics_router,
        "settings",
        SimpleNamespace(data_backend="files", database_url=""),
    )
    monkeypatch.setattr(
        analytics_router,
        "_published_json",
        lambda _prefix: payload_path,
    )

    response = client.get(
        "/api/v1/analytics/by-municipality"
        "?metric=admissions_per_100k&limit=10"
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["normalization_available"] is True
    assert payload["ranking_metric"] == "admissions_per_100k"
    assert [item["municipio_nome"] for item in payload["items"]] == [
        "Município B",
        "Município A",
    ]
