from fastapi.testclient import TestClient

import src.api.routers.analytics as analytics_router
import src.api.routers.overview as overview_router
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


def test_published_overview_is_served():
    response = client.get("/api/v1/indicators/overview")
    assert response.status_code == 200

    payload = response.json()
    assert payload["competence"] == "202607"
    assert payload["admissions"] == 19253
    assert payload["dismissals"] == 18347
    assert payload["balance"] == 906
    assert payload["admissions"] - payload["dismissals"] == payload["balance"]


def test_published_analytics_are_served():
    by_uf = client.get("/api/v1/analytics/by-uf")
    assert by_uf.status_code == 200
    assert by_uf.json()["competence"] == "202607"
    assert len(by_uf.json()["items"]) == 27

    by_occupation = client.get("/api/v1/analytics/by-occupation")
    assert by_occupation.status_code == 200
    assert by_occupation.json()["competence"] == "202607"
    assert by_occupation.json()["items"]

    comparison = client.get("/api/v1/analytics/territorial-comparison")
    assert comparison.status_code == 200
    payload = comparison.json()
    assert payload["competence"] == "202607"
    by_key = {item["key"]: item for item in payload["items"]}
    assert by_key["BR"]["admissions"] == 19253
    assert by_key["NE"]["admissions"] == 1951
    assert by_key["CE"]["admissions"] == 522
    assert by_key["NE"]["balance"] == 155
    assert by_key["CE"]["balance"] == 107


def test_overview_refuses_without_published_release(monkeypatch):
    monkeypatch.setattr(
        overview_router,
        "latest_published_competence",
        lambda _gold_path: None,
    )

    response = client.get("/api/v1/indicators/overview")
    assert response.status_code == 503
    assert "não publica números" in response.json()["detail"]


def test_analytics_refuse_without_published_release(monkeypatch):
    monkeypatch.setattr(
        analytics_router,
        "latest_published_competence",
        lambda _gold_path: None,
    )

    by_uf = client.get("/api/v1/analytics/by-uf")
    assert by_uf.status_code == 503
    assert "processado, validado e aprovado" in by_uf.json()["detail"]

    by_occupation = client.get("/api/v1/analytics/by-occupation")
    assert by_occupation.status_code == 503
    assert "processado, validado e aprovado" in by_occupation.json()["detail"]
