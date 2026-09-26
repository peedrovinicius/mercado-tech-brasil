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


def publication_registry(gold_path: Path) -> list[dict[str, object]]:
    releases: list[dict[str, object]] = []

    for gate_path in sorted(gold_path.glob("publication-gate-*.json")):
        try:
            payload = json.loads(gate_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        competence = str(payload.get("competence") or "")
        if len(competence) != 6 or not competence.isdigit():
            continue

        releases.append(
            {
                "competence": competence,
                "automatic_checks_passed": bool(
                    payload.get("automatic_checks_passed")
                ),
                "manual_approval_valid": bool(
                    payload.get("manual_approval_valid")
                ),
                "publishable": payload.get("publishable") is True,
                "source_sha256": payload.get("source_sha256"),
                "generated_at_utc": payload.get("generated_at_utc"),
            }
        )

    return sorted(releases, key=lambda item: str(item["competence"]))
