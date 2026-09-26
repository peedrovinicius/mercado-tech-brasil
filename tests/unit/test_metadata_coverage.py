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


def test_releases_expose_publication_state(monkeypatch, tmp_path: Path):
    (tmp_path / "publication-gate-202601.json").write_text(
        """{
          "competence": "202601",
          "automatic_checks_passed": true,
          "manual_approval_valid": false,
          "publishable": false,
          "source_sha256": "sha-jan",
          "generated_at_utc": "2026-09-26T08:00:00+00:00"
        }""",
        encoding="utf-8",
    )
    (tmp_path / "publication-gate-202602.json").write_text(
        """{
          "competence": "202602",
          "automatic_checks_passed": true,
          "manual_approval_valid": true,
          "publishable": true,
          "source_sha256": "sha-fev",
          "generated_at_utc": "2026-09-26T08:01:00+00:00"
        }""",
        encoding="utf-8",
    )

    fake_settings = SimpleNamespace(gold_path=tmp_path)
    monkeypatch.setattr(metadata_router, "settings", fake_settings)

    response = client.get("/api/v1/metadata/releases")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 2
    assert payload["published_count"] == 1
    assert payload["published_competencies"] == ["202602"]
    assert payload["latest_published_competence"] == "202602"
    assert payload["items"][0]["automatic_checks_passed"] is True
    assert payload["items"][0]["publishable"] is False
