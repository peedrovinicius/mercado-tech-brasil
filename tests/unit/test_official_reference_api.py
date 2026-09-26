from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_official_reference_july_2026_is_exposed():
    response = client.get("/api/v1/metadata/official-reference/202607")

    assert response.status_code == 200
    payload = response.json()
    assert payload["competence"] == "202607"
    assert payload["national"]["balance"] == 58568
    assert payload["ufs"]["CE"]["balance"] == 4181
    assert payload["source"]["owner"] == "Ministério do Trabalho e Emprego"
