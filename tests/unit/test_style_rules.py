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


def test_repository_does_not_use_long_dashes():
    root = Path(".")
    violations: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", "node_modules", "dist", ".venv"} for part in path.parts):
            continue

        text = path.read_text(encoding="utf-8")
        if "—" in text or "–" in text:
            violations.append(str(path))

    assert violations == []
