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


def test_repository_does_not_use_long_dashes():
    root = Path(".")
    violations: list[str] = []

    forbidden = tuple(chr(codepoint) for codepoint in LONG_DASH_CODEPOINTS)

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(
            part in {".git", "node_modules", "dist", ".venv"}
            for part in path.parts
        ):
            continue

        text = path.read_text(encoding="utf-8")
        if any(character in text for character in forbidden):
            violations.append(str(path))

    assert violations == []
