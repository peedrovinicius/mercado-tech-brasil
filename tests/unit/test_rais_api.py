import json
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

import src.api.routers.rais as rais_router
from src.api.main import app

client = TestClient(app)


def _write(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _use_blocked_rais_release(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "rais-publication-gate-2025.json",
        {
            "year": 2025,
            "automatic_checks_passed": True,
            "manual_approval_valid": False,
            "publishable": False,
            "release_sha256": "a" * 64,
        },
    )
    monkeypatch.setattr(
        rais_router,
        "settings",
        replace(rais_router.settings, gold_path=tmp_path),
    )


def test_rais_metrics_remain_blocked_while_release_is_unpublished(
    monkeypatch,
    tmp_path: Path,
):
    _use_blocked_rais_release(monkeypatch, tmp_path)

    response = client.get("/api/v1/rais/overview")

    assert response.status_code == 503
    assert "revisão metodológica" in response.json()["detail"]


def test_rais_specific_unpublished_year_returns_404(
    monkeypatch,
    tmp_path: Path,
):
    _use_blocked_rais_release(monkeypatch, tmp_path)

    response = client.get("/api/v1/rais/overview?year=2025")

    assert response.status_code == 404
    assert "ainda não está publicada" in response.json()["detail"]


def test_rais_release_registry_exposes_gate_state_without_metrics(
    monkeypatch,
    tmp_path: Path,
):
    _use_blocked_rais_release(monkeypatch, tmp_path)

    response = client.get("/api/v1/rais/releases")

    assert response.status_code == 200
    payload = response.json()
    assert payload["published_years"] == []
    assert payload["latest_published_year"] is None

    by_year = {int(item["year"]): item for item in payload["items"]}
    assert by_year[2025]["automatic_checks_passed"] is True
    assert by_year[2025]["manual_approval_valid"] is False
    assert by_year[2025]["publishable"] is False


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
        tmp_path / "rais-by-municipality-2025.json",
        {
            "year": 2025,
            "items": [
                {
                    "municipio_codigo_rais": "355030",
                    "municipio_codigo_ibge": "3550308",
                    "municipio_nome": "São Paulo",
                    "uf": "SP",
                    "active_stock": 8,
                    "share_of_tech_stock": 0.8,
                },
                {
                    "municipio_codigo_rais": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "active_stock": 2,
                    "share_of_tech_stock": 0.2,
                },
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
        rais_router,
        "settings",
        replace(rais_router.settings, gold_path=tmp_path),
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

    by_municipality = client.get("/api/v1/rais/by-municipality?limit=1")
    assert by_municipality.status_code == 200
    assert by_municipality.json()["items"][0]["municipio_nome"] == "São Paulo"
    assert by_municipality.json()["items"][0]["active_stock"] == 8


def test_rais_2025_repository_release_is_published():
    releases = client.get("/api/v1/rais/releases")

    assert releases.status_code == 200
    registry = releases.json()
    assert 2025 in registry["published_years"]

    by_year = {int(item["year"]): item for item in registry["items"]}
    assert by_year[2025]["automatic_checks_passed"] is True
    assert by_year[2025]["manual_approval_valid"] is True
    assert by_year[2025]["publishable"] is True

    overview = client.get("/api/v1/rais/overview?year=2025")
    assert overview.status_code == 200
    assert overview.json()["active_stock_tech"] == 786_296
    assert overview.json()["active_stock_national_reference"] == 59_970_945

    by_uf = client.get("/api/v1/rais/by-uf?year=2025")
    assert by_uf.status_code == 200
    assert sum(item["active_stock"] for item in by_uf.json()["items"]) == 786_296

    by_family = client.get("/api/v1/rais/by-cbo-family?year=2025")
    assert by_family.status_code == 200
    assert sum(item["active_stock"] for item in by_family.json()["items"]) == 786_296

    by_municipality = client.get("/api/v1/rais/by-municipality?year=2025&limit=1")
    assert by_municipality.status_code == 200
    assert by_municipality.json()["items"][0]["active_stock"] > 0


def test_rais_year_parameter_is_validated():
    response = client.get("/api/v1/rais/overview?year=1800")
    assert response.status_code == 422
