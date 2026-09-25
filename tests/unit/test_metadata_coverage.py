from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import src.api.routers.metadata as metadata_router
from src.api.main import app

client = TestClient(app)


def test_coverage_finds_nested_manifests(monkeypatch, tmp_path: Path):
    nested = tmp_path / "202607" / "extracted"
    nested.mkdir(parents=True)

    (nested / "CAGEDMOV.txt.manifest.json").write_text(
        """{
          "source": "novo_caged_mov_local",
          "competence": "202607",
          "original_name": "CAGEDMOV.txt",
          "size_bytes": 123,
          "sha256": "abc",
          "ingested_at_utc": "2026-09-25T20:00:00+00:00"
        }""",
        encoding="utf-8",
    )

    fake_settings = SimpleNamespace(bronze_path=tmp_path)
    monkeypatch.setattr(metadata_router, "settings", fake_settings)

    response = client.get("/api/v1/metadata/coverage")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "loaded"
    assert payload["competencies"] == ["202607"]
    assert payload["files"][0]["sha256"] == "abc"
