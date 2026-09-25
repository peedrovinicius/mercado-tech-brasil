from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["project"] == "Mercado Tech Brasil"


def test_sources_are_exposed():
    response = client.get("/api/v1/metadata/sources")
    assert response.status_code == 200
    payload = response.json()
    assert "novo_caged" in payload
    assert "cbo" in payload
    assert "ibge" in payload


def test_overview_refuses_to_invent_data():
    response = client.get("/api/v1/indicators/overview")
    assert response.status_code == 503
    assert "não publica números" in response.json()["detail"]


def test_by_uf_refuses_to_invent_data():
    response = client.get("/api/v1/analytics/by-uf")
    assert response.status_code == 503
    assert "pipeline oficial" in response.json()["detail"]


def test_by_occupation_refuses_to_invent_data():
    response = client.get("/api/v1/analytics/by-occupation")
    assert response.status_code == 503
    assert "pipeline oficial" in response.json()["detail"]
