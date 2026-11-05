import pytest

from scripts import smoke_production


def _install_fake_production(monkeypatch: pytest.MonkeyPatch) -> None:
    secure_headers = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "camera=(), microphone=(), geolocation=()",
        "cross-origin-opener-policy": "same-origin",
    }
    responses = {
        "/api/v1/system/health": (
            {"status": "ok", "version": "0.40.0"},
            secure_headers,
        ),
        "/api/v1/system/readiness": (
            {"api": "ready", "data_loaded": True, "published_competence": "202608"},
            {},
        ),
        "/api/v1/system/release": (
            {
                "version": "0.40.0",
                "monthly": {
                    "latest_competence": "202608",
                    "policy_max_competence": "202609",
                },
                "rais": {"latest_published_year": 2025},
            },
            {},
        ),
        "/api/v1/indicators/overview": (
            {
                "competence": "202608",
                "admissions": 2,
                "dismissals": 1,
                "balance": 1,
            },
            {},
        ),
        "/api/v1/rais/overview": (
            {"year": 2025, "active_stock_tech": 1},
            {},
        ),
    }

    def fake_json(base_url: str, path: str):
        assert base_url == "https://test.example"
        return responses[path]

    def fake_request(base_url: str, path: str):
        if path == "/docs":
            return 200, {}, b"Swagger UI"
        if path == "/":
            return 200, {}, b"Mercado Tech Brasil"
        pytest.fail(f"Unexpected non-JSON path: {path}")

    monkeypatch.setattr(smoke_production, "_json", fake_json)
    monkeypatch.setattr(smoke_production, "_request", fake_request)


def test_smoke_allows_unpublished_month_in_audit_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_production(monkeypatch)
    result = smoke_production.validate(
        base_url="https://test.example",
        expected_version="0.40.0",
        expected_monthly="202608",
        expected_policy_max="202609",
        expected_rais_year=2025,
    )
    assert result["status"] == "ok"
    assert result["monthly"] == "202608"


def test_smoke_rejects_unexpected_audit_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_production(monkeypatch)
    with pytest.raises(RuntimeError, match="Cobertura"):
        smoke_production.validate(
            base_url="https://test.example",
            expected_version="0.40.0",
            expected_monthly="202608",
            expected_policy_max="202610",
            expected_rais_year=2025,
        )
