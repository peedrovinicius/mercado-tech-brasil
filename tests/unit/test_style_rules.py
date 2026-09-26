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

    assert versions == {"0.19.3"}
