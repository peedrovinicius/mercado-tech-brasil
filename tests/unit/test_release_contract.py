import json
import tomllib
from pathlib import Path

import yaml

from src.core.settings import settings

ROOT = Path(__file__).resolve().parents[2]


def test_release_versions_and_notes_are_aligned():
    pyproject = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    package = json.loads(
        (ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
    )

    version = pyproject["project"]["version"]
    assert version == settings.version
    assert version == package["version"]

    notes = ROOT / "docs" / "releases" / f"v{version}.md"
    assert notes.exists()
    assert notes.stat().st_size > 0
    assert f"v{version}" in notes.read_text(encoding="utf-8")


def test_render_blueprint_keeps_governed_production_contract():
    payload = yaml.safe_load(
        (ROOT / "render.yaml").read_text(encoding="utf-8")
    )
    services = payload["services"]
    assert len(services) == 1

    service = services[0]
    assert service["type"] == "web"
    assert service["runtime"] == "python"
    assert service["branch"] == "main"
    assert service["healthCheckPath"] == "/api/v1/system/health"
    assert service["autoDeployTrigger"] == "checksPass"

    paths = set(service["buildFilter"]["paths"])
    assert "src/**" in paths
    assert "frontend/**" in paths
    assert "data/gold/**" in paths
    assert "docs/**" not in paths
