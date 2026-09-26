import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import src.api.routers.system as system_router
from src.api.main import app

client = TestClient(app)


def _settings(tmp_path: Path):
    return SimpleNamespace(
        gold_path=tmp_path,
        data_backend="files",
    )


def _gate(tmp_path: Path, publishable: bool) -> None:
    (tmp_path / "publication-gate-202607.json").write_text(
        json.dumps(
            {
                "competence": "202607",
                "publishable": publishable,
            }
        ),
        encoding="utf-8",
    )


def test_readiness_requires_approved_gate_and_matching_gold(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(system_router, "settings", _settings(tmp_path))

    (tmp_path / "overview-202607.json").write_text("{}", encoding="utf-8")
    (tmp_path / "market-202607.parquet").write_bytes(b"placeholder")

    _gate(tmp_path, False)
    payload = client.get("/api/v1/system/readiness").json()
    assert payload["data_loaded"] is False

    _gate(tmp_path, True)
    payload = client.get("/api/v1/system/readiness").json()
    assert payload["data_loaded"] is True
    assert payload["published_competence"] == "202607"
    assert payload["latest_overview"] == "overview-202607.json"
    assert payload["latest_market"] == "market-202607.parquet"


def test_readiness_stays_false_when_approved_artifact_is_missing(
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(system_router, "settings", _settings(tmp_path))
    _gate(tmp_path, True)

    assert client.get("/api/v1/system/readiness").json()["data_loaded"] is False
