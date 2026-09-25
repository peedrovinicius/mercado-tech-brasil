from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import src.api.routers.system as system_router
from src.api.main import app

client = TestClient(app)


def test_readiness_requires_overview_and_market(monkeypatch, tmp_path: Path):
    fake_settings = SimpleNamespace(gold_path=tmp_path)
    monkeypatch.setattr(system_router, "settings", fake_settings)

    response = client.get("/api/v1/system/readiness")
    assert response.status_code == 200
    assert response.json()["data_loaded"] is False

    (tmp_path / "quality-202607.json").write_text("{}", encoding="utf-8")
    assert client.get("/api/v1/system/readiness").json()["data_loaded"] is False

    (tmp_path / "overview-202607.json").write_text("{}", encoding="utf-8")
    assert client.get("/api/v1/system/readiness").json()["data_loaded"] is False

    (tmp_path / "market-202607.parquet").write_bytes(b"placeholder")
    payload = client.get("/api/v1/system/readiness").json()
    assert payload["data_loaded"] is True
    assert payload["latest_overview"] == "overview-202607.json"
    assert payload["latest_market"] == "market-202607.parquet"
