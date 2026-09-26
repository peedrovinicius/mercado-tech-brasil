from __future__ import annotations

import json
from pathlib import Path


def published_competencies(gold_path: Path) -> list[str]:
    competencies: list[str] = []

    for gate_path in gold_path.glob("publication-gate-*.json"):
        try:
            payload = json.loads(gate_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        competence = str(payload.get("competence") or "")
        if (
            payload.get("publishable") is True
            and len(competence) == 6
            and competence.isdigit()
        ):
            competencies.append(competence)

    return sorted(set(competencies))


def latest_published_competence(gold_path: Path) -> str | None:
    competencies = published_competencies(gold_path)
    return competencies[-1] if competencies else None


def published_json_path(
    gold_path: Path,
    *,
    prefix: str,
    competence: str,
) -> Path | None:
    path = gold_path / f"{prefix}-{competence}.json"
    return path if path.exists() else None
