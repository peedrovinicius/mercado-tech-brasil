import json
from pathlib import Path

from fastapi.testclient import TestClient

import src.api.routers.rais as rais_router
from src.api.main import app

client = TestClient(app)


def test_rais_metrics_remain_blocked_while_release_is_unpublished():
    response = client.get("/api/v1/rais/overview")

    assert response.status_code == 503
    assert "revisão metodológica" in response.json()["detail"]


def test_rais_specific_unpublished_year_returns_404():
    response = client.get("/api/v1/rais/overview?year=2025")

    assert response.status_code == 404
    assert "ainda não está publicada" in response.json()["detail"]


def test_rais_release_registry_exposes_gate_state_without_metrics():
    response = client.get("/api/v1/rais/releases")

    assert response.status_code == 200
    payload = response.json()
    assert payload["published_years"] == []
    assert payload["latest_published_year"] is None

    by_year = {int(item["year"]): item for item in payload["items"]}
    assert by_year[2025]["automatic_checks_passed"] is True
    assert by_year[2025]["manual_approval_valid"] is False
    assert by_year[2025]["publishable"] is False


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def test_rais_endpoints_serve_only_after_published_gate(
    monkeypatch,
    tmp_path: Path,
):
    _write(
        tmp_path / "rais-overview-2025.json",
        {
            "year": 2025,
            "active_stock_tech": 10,
            "publication_ready": False,
        },
    )
    _write(
        tmp_path / "rais-by-uf-2025.json",
        {
            "year": 2025,
            "items": [
                {"uf": "SP", "active_stock": 8},
                {"uf": "CE", "active_stock": 2},
            ],
        },
    )
    _write(
        tmp_path / "rais-by-cbo-family-2025.json",
        {
            "year": 2025,
            "items": [
                {"cbo_familia": "2124", "active_stock": 7},
                {"cbo_familia": "3171", "active_stock": 3},
            ],
        },
    )
    _write(
        tmp_path / "rais-publication-gate-2025.json",
        {
            "year": 2025,
            "automatic_checks_passed": True,
            "manual_approval_valid": True,
            "publishable": True,
            "release_sha256": "a" * 64,
        },
    )

    monkeypatch.setattr(
        rais_router.settings,
        "gold_path",
        tmp_path,
    )

    overview = client.get("/api/v1/rais/overview")
    assert overview.status_code == 200
    assert overview.json()["active_stock_tech"] == 10

    by_uf = client.get("/api/v1/rais/by-uf?limit=1")
    assert by_uf.status_code == 200
    assert by_uf.json()["items"] == [
        {"uf": "SP", "active_stock": 8}
    ]

    by_family = client.get("/api/v1/rais/by-cbo-family?limit=1")
    assert by_family.status_code == 200
    assert by_family.json()["items"] == [
        {"cbo_familia": "2124", "active_stock": 7}
    ]


def test_rais_year_parameter_is_validated():
    response = client.get("/api/v1/rais/overview?year=1800")
    assert response.status_code == 422
