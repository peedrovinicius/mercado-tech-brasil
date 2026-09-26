from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_exposes_api_metadata_without_built_frontend():
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"] == "Mercado Tech Brasil"
    assert payload["health"] == "/api/v1/system/health"


def test_swagger_remains_available():
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()
