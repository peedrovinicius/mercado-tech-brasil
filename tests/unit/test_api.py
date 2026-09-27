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
    assert payload["version"] == "0.40.0"


def test_release_state_exposes_governed_baseline():
    response = client.get("/api/v1/system/release")
    assert response.status_code == 200
    payload = response.json()

    assert payload["project"] == "Mercado Tech Brasil"
    assert payload["version"] == "0.40.0"
    assert payload["monthly"]["published_count"] == 7
    assert payload["monthly"]["first_competence"] == "202601"
    assert payload["monthly"]["latest_competence"] == "202607"
    assert payload["monthly"]["policy_mode"] == "locked"
    assert payload["monthly"]["policy_max_competence"] == "202607"
    assert payload["rais"]["latest_published_year"] == 2025


def test_security_headers_are_present():
    response = client.get("/api/v1/system/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert (
        response.headers["referrer-policy"]
        == "strict-origin-when-cross-origin"
    )
    assert (
        response.headers["permissions-policy"]
        == "camera=(), microphone=(), geolocation=()"
    )
    assert response.headers["cross-origin-opener-policy"] == "same-origin"


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

    by_municipality = client.get("/api/v1/analytics/by-municipality?limit=15")
    assert by_municipality.status_code == 200
    assert by_municipality.json()["ranking_metric"] == "admissions"

    normalized = client.get(
        "/api/v1/analytics/by-municipality"
        "?limit=15&metric=admissions_per_100k"
    )
    assert normalized.status_code == 200
    normalized_payload = normalized.json()
    assert normalized_payload["ranking_metric"] == "admissions_per_100k"
    if normalized_payload["normalization_available"]:
        assert normalized_payload["items"]
        assert all(
            item["admissions_per_100k"] is not None
            and item["population_estimate"] is not None
            and item["population_estimate"] > 0
            for item in normalized_payload["items"]
        )
    else:
        assert normalized_payload["items"] == []

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

    stock_flow = client.get("/api/v1/analytics/stock-flow-context")
    assert stock_flow.status_code == 200
    stock_flow_payload = stock_flow.json()
    assert stock_flow_payload["rais_year"] == 2025
    assert stock_flow_payload["stock_reference_date"] == "2025-12-31"
    assert stock_flow_payload["caged_from"] == "202601"
    assert stock_flow_payload["caged_to"] == "202607"
    assert stock_flow_payload["published_months"] == 7
    assert stock_flow_payload["totals"]["active_stock"] == 786296
    assert stock_flow_payload["totals"]["admissions"] == 134209
    assert stock_flow_payload["totals"]["dismissals"] == 127865
    assert stock_flow_payload["totals"]["balance"] == 6344
    stock_flow_families = {
        item["cbo_familia"]: item
        for item in stock_flow_payload["families"]
    }
    assert stock_flow_families["3172"]["active_stock"] == 121680
    assert stock_flow_families["3172"]["admissions"] == 31132
    assert stock_flow_families["3172"]["balance"] == 5232
    assert round(
        stock_flow_families["3172"]["composition_gap_pp"],
        2,
    ) == 7.72

    occupation_trend = client.get(
        "/api/v1/analytics/occupation-family-trend"
    )
    assert occupation_trend.status_code == 200
    occupation_payload = occupation_trend.json()
    assert occupation_payload["published_months"] == 7
    assert len(occupation_payload["families"]) == 5
    assert {
        item["cbo_familia"]
        for item in occupation_payload["families"]
    } == {"2122", "2123", "2124", "3171", "3172"}
    assert sum(
        item["admissions"]
        for item in occupation_payload["families"]
    ) == 134209
    assert sum(
        item["dismissals"]
        for item in occupation_payload["families"]
    ) == 127865
    assert sum(
        item["balance"]
        for item in occupation_payload["families"]
    ) == 6344
    assert all(
        len(item["monthly"]) == 7
        for item in occupation_payload["families"]
    )

    temporal = client.get("/api/v1/analytics/temporal-summary")
    assert temporal.status_code == 200
    temporal_payload = temporal.json()
    assert temporal_payload["published_months"] == 7
    assert temporal_payload["cumulative"] == {
        "admissions": 134209,
        "dismissals": 127865,
        "balance": 6344,
    }

    periods = {item["key"]: item for item in temporal_payload["periods"]}
    assert periods["2026Q1"]["admissions"] == 58179
    assert periods["2026Q1"]["balance"] == 2942
    assert periods["2026Q1"]["complete"] is True
    assert periods["2026Q2"]["admissions"] == 56777
    assert periods["2026Q2"]["balance"] == 2496
    assert periods["2026Q2"]["complete"] is True
    assert periods["2026Q3"]["published_months"] == 1
    assert periods["2026Q3"]["balance"] == 906
    assert periods["2026Q3"]["complete"] is False


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


def test_municipality_rejects_unknown_ranking_metric():
    response = client.get(
        "/api/v1/analytics/by-municipality?metric=salary_mean_admissions"
    )
    assert response.status_code == 422
