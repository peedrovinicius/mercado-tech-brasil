import json
import re
import tomllib
from pathlib import Path

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
    ".svg",
}

LONG_DASH_CODEPOINTS = (0x2013, 0x2014)
IGNORED_PARTS = {".git", "node_modules", "dist", ".venv"}


def iter_repository_text_files():
    root = Path(".")

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        yield path


def test_repository_does_not_use_long_dashes():
    violations: list[str] = []
    forbidden = tuple(chr(codepoint) for codepoint in LONG_DASH_CODEPOINTS)

    for path in iter_repository_text_files():
        text = path.read_text(encoding="utf-8")
        if any(character in text for character in forbidden):
            violations.append(str(path))

    assert violations == []


def test_published_scope_does_not_reintroduce_excluded_period():
    violations: list[str] = []
    forbidden_tokens = (
        "2026" + "08",
        "agos" + "to",
        "Ago" + "/2026",
    )

    for path in iter_repository_text_files():
        text = path.read_text(encoding="utf-8")
        if any(token.lower() in text.lower() for token in forbidden_tokens):
            violations.append(str(path))

    assert violations == []


def test_project_versions_are_aligned():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    frontend = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))
    settings_text = Path("src/core/settings.py").read_text(encoding="utf-8")

    match = re.search(r'version: str = "([^"]+)"', settings_text)
    assert match is not None

    versions = {
        pyproject["project"]["version"],
        frontend["version"],
        match.group(1),
    }

    assert len(versions) == 1


def test_production_docs_match_render_serving_backend():
    render = Path("render.yaml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    deploy = Path("docs/DEPLOY.md").read_text(encoding="utf-8")
    architecture = Path("docs/ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "value: files" in render
    assert "| Serving de produção | Arquivos Gold publicados |" in readme
    assert "- serving ativo: arquivos Gold publicados" in status
    assert "DATA_BACKEND=files" in deploy
    assert "DATA_BACKEND=files" in architecture
    assert "| PostgreSQL gerenciado | Provisionado |" not in readme


def test_readme_dashboard_asset_is_versioned():
    readme = Path("README.md").read_text(encoding="utf-8")
    dashboard = Path("assets/readme-dashboard.svg")

    assert dashboard.exists()
    assert 'src="assets/readme-dashboard.svg"' in readme

    svg = dashboard.read_text(encoding="utf-8")
    assert "134.209" in svg
    assert "127.865" in svg
    assert "+6.344" in svg
    assert "10,13%" in svg
    assert "26,76%" in svg
