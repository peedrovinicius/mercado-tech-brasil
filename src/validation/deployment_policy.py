from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


MONTHLY_RE = re.compile(r"(20\d{4})(?=\.[^.]+$)")
RAIS_RE = re.compile(r"rais-[^/]*-(20\d{2})(?=\.[^.]+$)")


@dataclass(frozen=True)
class DeploymentDecision:
    eligible: bool
    monthly_competencies: tuple[str, ...]
    rais_years: tuple[int, ...]
    reasons: tuple[str, ...]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_is_clean(payload: dict) -> bool:
    if (
        payload.get("publishable") is not True
        or payload.get("automatic_checks_passed") is not True
        or payload.get("manual_approval_valid") is not True
    ):
        return False

    checks = payload.get("checks")
    if not isinstance(checks, list):
        return False

    return all(
        not check.get("blocking", True) or check.get("passed") is True
        for check in checks
        if isinstance(check, dict)
    )


def _monthly_from_path(path: str) -> str | None:
    if not path.startswith("data/gold/") or "/rais-" in path:
        return None
    match = MONTHLY_RE.search(path)
    return match.group(1) if match else None


def _rais_from_path(path: str) -> int | None:
    if not path.startswith("data/gold/"):
        return None
    match = RAIS_RE.search(path)
    return int(match.group(1)) if match else None


def evaluate_deployment_changes(
    *,
    changed_paths: list[str],
    gold_dir: Path,
) -> DeploymentDecision:
    monthly = sorted(
        {
            competence
            for path in changed_paths
            if (competence := _monthly_from_path(path)) is not None
        }
    )
    rais_years = sorted(
        {
            year
            for path in changed_paths
            if (year := _rais_from_path(path)) is not None
        }
    )

    reasons: list[str] = []

    for competence in monthly:
        gate_path = gold_dir / f"publication-gate-{competence}.json"
        if not gate_path.exists():
            reasons.append(
                f"{competence}: gate mensal ausente."
            )
            continue
        gate = _read_json(gate_path)
        if str(gate.get("competence") or "") != competence:
            reasons.append(
                f"{competence}: competência do gate mensal diverge."
            )
        elif not _gate_is_clean(gate):
            reasons.append(
                f"{competence}: release mensal ainda não está publicável."
            )

    for year in rais_years:
        gate_path = gold_dir / f"rais-publication-gate-{year}.json"
        if not gate_path.exists():
            reasons.append(f"{year}: gate anual RAIS ausente.")
            continue
        gate = _read_json(gate_path)
        if int(gate.get("year") or 0) != year:
            reasons.append(f"{year}: ano do gate RAIS diverge.")
        elif not _gate_is_clean(gate):
            reasons.append(
                f"{year}: release anual RAIS ainda não está publicável."
            )

    return DeploymentDecision(
        eligible=not reasons,
        monthly_competencies=tuple(monthly),
        rais_years=tuple(rais_years),
        reasons=tuple(reasons),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida se alterações de dados podem chegar à produção."
    )
    parser.add_argument(
        "--changed-files",
        type=Path,
        required=True,
        help="Arquivo com um caminho alterado por linha.",
    )
    parser.add_argument(
        "--gold-dir",
        type=Path,
        default=Path("data/gold"),
    )
    args = parser.parse_args()

    paths = [
        line.strip()
        for line in args.changed_files.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    decision = evaluate_deployment_changes(
        changed_paths=paths,
        gold_dir=args.gold_dir,
    )

    print(
        "deployment policy:",
        f"eligible={decision.eligible}",
        f"monthly={list(decision.monthly_competencies)}",
        f"rais={list(decision.rais_years)}",
    )
    for reason in decision.reasons:
        print(f"BLOCK: {reason}")

    raise SystemExit(0 if decision.eligible else 2)


if __name__ == "__main__":
    main()
