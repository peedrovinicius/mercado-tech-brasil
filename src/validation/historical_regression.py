from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.api.publication import published_competencies

SERVING_ARTIFACT_TEMPLATES = (
    "overview-{competence}.json",
    "by-uf-{competence}.json",
    "by-occupation-{competence}.json",
    "by-municipality-{competence}.json",
    "market-{competence}.parquet",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON inválido: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def snapshot_published_history(gold_dir: Path) -> dict[str, Any]:
    artifacts: dict[str, dict[str, str]] = {}
    overview_metrics: dict[str, dict[str, object]] = {}

    for competence in published_competencies(gold_dir):
        files: dict[str, str] = {}
        for template in SERVING_ARTIFACT_TEMPLATES:
            name = template.format(competence=competence)
            path = gold_dir / name
            if not path.exists():
                raise FileNotFoundError(
                    f"Artefato publicado ausente no baseline: {path}"
                )
            files[name] = _sha256(path)

        overview = _read_json(gold_dir / f"overview-{competence}.json")
        overview_metrics[competence] = {
            "admissions": overview.get("admissions"),
            "dismissals": overview.get("dismissals"),
            "balance": overview.get("balance"),
            "salary_median_admissions_real": overview.get(
                "salary_median_admissions_real"
            ),
        }
        artifacts[competence] = files

    return {
        "version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "published_competencies": sorted(artifacts),
        "artifacts": artifacts,
        "overview_metrics": overview_metrics,
    }


def write_history_snapshot(snapshot: dict[str, Any], destination: Path) -> None:
    _write_json(destination, snapshot)


def _adjustment_effective_competencies(
    silver_dir: Path,
    ingest_competence: str,
) -> set[str]:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError("Polars não está instalado.") from exc

    result: set[str] = set()
    for kind in ("for", "exc"):
        path = silver_dir / f"caged_tech_{kind}_{ingest_competence}.parquet"
        if not path.exists():
            continue
        frame = pl.read_parquet(path, columns=["effective_competence"])
        for value in frame["effective_competence"].drop_nulls().unique().to_list():
            competence = str(value)
            if len(competence) == 6 and competence.isdigit():
                result.add(competence)
    return result


def evaluate_history_revisions(
    *,
    ingest_competence: str,
    baseline_path: Path,
    gold_dir: Path,
    silver_dir: Path,
    package_root: Path,
) -> dict[str, Any]:
    baseline = _read_json(baseline_path)
    baseline_artifacts = baseline.get("artifacts")
    if not isinstance(baseline_artifacts, dict):
        raise TypeError("Baseline histórico sem mapa de artefatos.")

    adjustment_competencies = _adjustment_effective_competencies(
        silver_dir,
        ingest_competence,
    )
    future_adjustments = sorted(
        competence
        for competence in adjustment_competencies
        if competence > ingest_competence
    )

    changed: dict[str, list[dict[str, str | None]]] = {}
    missing_after: list[str] = []

    for competence, raw_files in baseline_artifacts.items():
        if not isinstance(raw_files, dict):
            raise TypeError(
                f"Baseline histórico inválido para {competence}."
            )

        changes: list[dict[str, str | None]] = []
        for name, before_sha in raw_files.items():
            path = gold_dir / name
            if not path.exists():
                missing_after.append(name)
                changes.append(
                    {
                        "file": name,
                        "before_sha256": str(before_sha),
                        "after_sha256": None,
                    }
                )
                continue

            after_sha = _sha256(path)
            if after_sha != before_sha:
                changes.append(
                    {
                        "file": name,
                        "before_sha256": str(before_sha),
                        "after_sha256": after_sha,
                    }
                )

        if changes:
            changed[str(competence)] = changes

    allowed = set(adjustment_competencies)
    if ingest_competence in baseline_artifacts:
        allowed.add(ingest_competence)

    unexpected = sorted(set(changed) - allowed)
    passed = not unexpected and not future_adjustments and not missing_after

    package_dir = package_root / ingest_competence / "gold"
    if package_dir.parent.exists():
        shutil.rmtree(package_dir.parent)

    packaged: list[dict[str, str]] = []
    if passed:
        for competence in sorted(changed):
            if competence == ingest_competence:
                continue

            package_dir.mkdir(parents=True, exist_ok=True)
            raw_files = baseline_artifacts[competence]
            for name, before_sha in raw_files.items():
                source = gold_dir / name
                destination = package_dir / name
                shutil.copy2(source, destination)
                packaged.append(
                    {
                        "competence": competence,
                        "file": name,
                        "before_sha256": str(before_sha),
                        "after_sha256": _sha256(source),
                    }
                )

    before_metrics = baseline.get("overview_metrics")
    overview_changes: dict[str, dict[str, object]] = {}
    if isinstance(before_metrics, dict):
        for competence in changed:
            before = before_metrics.get(competence)
            overview_path = gold_dir / f"overview-{competence}.json"
            after = _read_json(overview_path) if overview_path.exists() else {}
            overview_changes[competence] = {
                "before": before,
                "after": {
                    "admissions": after.get("admissions"),
                    "dismissals": after.get("dismissals"),
                    "balance": after.get("balance"),
                    "salary_median_admissions_real": after.get(
                        "salary_median_admissions_real"
                    ),
                },
            }

    result = {
        "version": 1,
        "ingest_competence": ingest_competence,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "passed": passed,
        "adjustment_effective_competencies": sorted(
            adjustment_competencies
        ),
        "changed_published_competencies": sorted(changed),
        "unexpected_changed_competencies": unexpected,
        "future_adjustment_competencies": future_adjustments,
        "missing_after": sorted(missing_after),
        "changes": changed,
        "overview_changes": overview_changes,
        "packaged_files": packaged,
    }
    _write_json(
        gold_dir / f"revision-impact-{ingest_competence}.json",
        result,
    )
    return result


def apply_history_revision_package(
    *,
    ingest_competence: str,
    gold_dir: Path,
    package_root: Path,
) -> list[Path]:
    manifest_path = gold_dir / f"revision-impact-{ingest_competence}.json"
    manifest = _read_json(manifest_path)

    if manifest.get("passed") is not True:
        raise RuntimeError(
            "Manifesto de impacto histórico não foi aprovado na auditoria."
        )

    raw_files = manifest.get("packaged_files")
    if not isinstance(raw_files, list):
        raise TypeError("Manifesto de revisão sem packaged_files.")

    package_dir = package_root / ingest_competence / "gold"
    applied: list[Path] = []

    for item in raw_files:
        if not isinstance(item, dict):
            raise TypeError("Entrada inválida no pacote de revisão.")

        name = str(item.get("file") or "")
        if Path(name).name != name:
            raise ValueError(f"Caminho de revisão inválido: {name}")

        source = package_dir / name
        target = gold_dir / name
        before_sha = str(item.get("before_sha256") or "")
        after_sha = str(item.get("after_sha256") or "")

        if not source.exists():
            raise FileNotFoundError(
                f"Arquivo ausente no pacote de revisão: {source}"
            )
        if not target.exists():
            raise FileNotFoundError(
                f"Arquivo publicado ausente antes da revisão: {target}"
            )
        if _sha256(source) != after_sha:
            raise RuntimeError(
                f"Hash do pacote de revisão diverge para {name}."
            )
        if _sha256(target) != before_sha:
            raise RuntimeError(
                f"Baseline publicado mudou desde a auditoria: {name}."
            )

        shutil.copy2(source, target)
        applied.append(target)

    return applied
