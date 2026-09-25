from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.main import app
import src.api.routers.provenance as provenance_router

client = TestClient(app)


def test_latest_provenance_returns_manifest(monkeypatch, tmp_path: Path):
    nested = tmp_path / "bronze" / "202607" / "extracted"
    nested.mkdir(parents=True)
    manifest = nested / "CAGEDMOV.txt.manifest.json"
    manifest.write_text(
        """{
          "source": "novo_caged_mov_local",
          "competence": "202607",
          "original_name": "CAGEDMOV.txt",
          "size_bytes": 456,
          "sha256": "1234567890abcdef",
          "ingested_at_utc": "2026-09-25T20:00:00+00:00"
        }""",
        encoding="utf-8",
    )

    fake_settings = SimpleNamespace(
        bronze_path=tmp_path / "bronze",
        root=tmp_path,
    )
    monkeypatch.setattr(provenance_router, "settings", fake_settings)

    response = client.get("/api/v1/provenance/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["competence"] == "202607"
    assert payload["sha256"] == "1234567890abcdef"
    assert payload["original_name"] == "CAGEDMOV.txt"


def test_latest_provenance_404_without_manifest(monkeypatch, tmp_path: Path):
    fake_settings = SimpleNamespace(
        bronze_path=tmp_path,
        root=tmp_path,
    )
    monkeypatch.setattr(provenance_router, "settings", fake_settings)
    response = client.get("/api/v1/provenance/latest")
    assert response.status_code == 404
