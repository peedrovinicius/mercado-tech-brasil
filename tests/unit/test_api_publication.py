import json
from pathlib import Path

from src.api.publication import (
    latest_published_competence,
    published_competencies,
)


def _write_gate(path: Path, competence: str, publishable: bool) -> None:
    path.write_text(
        json.dumps(
            {
                "competence": competence,
                "publishable": publishable,
            }
        ),
        encoding="utf-8",
    )


def test_only_publishable_gates_are_visible(tmp_path: Path):
    _write_gate(
        tmp_path / "publication-gate-202606.json",
        "202606",
        True,
    )
    _write_gate(
        tmp_path / "publication-gate-202607.json",
        "202607",
        False,
    )

    assert published_competencies(tmp_path) == ["202606"]
    assert latest_published_competence(tmp_path) == "202606"


def test_no_approved_gate_returns_none(tmp_path: Path):
    _write_gate(
        tmp_path / "publication-gate-202607.json",
        "202607",
        False,
    )

    assert latest_published_competence(tmp_path) is None
