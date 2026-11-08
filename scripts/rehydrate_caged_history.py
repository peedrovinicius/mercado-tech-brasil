"""Rebuild published CAGED Silver from the original, verified MTE files.

This is a fail-closed, audit-only operation. It never publishes artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.cli import command_extract, command_transform
from src.core.settings import settings
from src.gold.aggregate import build_gold
from src.ingestion.https_caged import download_month_resilient, write_download_manifest
from src.transform.adjustments import transform_adjustment_file

KINDS = ("MOV", "FOR", "EXC")
OFFICIAL_PREFIX = "ftp://ftp.mtps.gov.br/pdet/microdados/"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Objeto JSON esperado: {path}")
    return payload


def _expected_manifests(
    competence: str,
    *,
    bronze_root: Path,
    approvals_path: Path,
) -> dict[str, dict[str, Any]]:
    approvals = _read_json(approvals_path)
    approval = approvals.get(competence)
    if not isinstance(approval, dict) or approval.get("approved") is not True:
        raise ValueError(f"Competência sem aprovação publicada: {competence}")

    expected: dict[str, dict[str, Any]] = {}
    for kind in KINDS:
        path = (
            bronze_root / competence / "extracted"
            / f"CAGED{kind}{competence}.txt.manifest.json"
        )
        payload = _read_json(path)
        digest = str(payload.get("sha256") or "")
        if (
            payload.get("competence") != competence
            or payload.get("source") != "novo_caged_mte"
            or payload.get("transport") != "ftp_mte"
            or not str(payload.get("source_url") or "").startswith(OFFICIAL_PREFIX)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or not isinstance(payload.get("size_bytes"), int)
            or payload["size_bytes"] <= 0
        ):
            raise ValueError(f"Manifesto oficial inválido: {path}")
        expected[kind] = payload

    if expected["MOV"]["sha256"] != approval.get("source_sha256"):
        raise ValueError(f"SHA-256 MOV difere da aprovação publicada: {competence}")
    return expected


def _verify_extracted(
    competence: str,
    *,
    kind: str,
    extracted_dir: Path,
    original: dict[str, Any],
) -> Path:
    expected_name = f"CAGED{kind}{competence}.txt"
    path = extracted_dir / expected_name
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo original não reconstituído: {path}")
    if path.stat().st_size != original["size_bytes"]:
        raise ValueError(f"Tamanho divergente do {kind} original: {competence}")
    if _sha256(path) != original["sha256"]:
        raise ValueError(f"SHA-256 divergente do {kind} original: {competence}")
    return path


def _compare_published_artifacts(
    baseline: dict[str, Any], gold_dir: Path
) -> list[dict[str, str | None]]:
    artifacts = baseline.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Baseline sem artefatos publicados.")

    differences: list[dict[str, str | None]] = []
    for competence, files in sorted(artifacts.items()):
        if not isinstance(files, dict) or not files:
            raise ValueError(f"Baseline inválida: {competence}")
        for name, expected in sorted(files.items()):
            if Path(name).name != name:
                raise ValueError(f"Caminho inválido na baseline: {name}")
            path = gold_dir / name
            actual = _sha256(path) if path.is_file() else None
            if actual != expected:
                differences.append(
                    {
                        "competence": competence,
                        "file": name,
                        "before_sha256": str(expected),
                        "after_sha256": actual,
                    }
                )
    return differences



def _compare_overview_metrics(
    baseline: dict[str, Any], gold_dir: Path
) -> list[dict[str, Any]]:
    """Distinguish historical numeric regressions from file hash changes."""
    original = baseline.get("overview_metrics")
    if not isinstance(original, dict):
        raise ValueError("Snapshot sem métricas históricas.")

    differences: list[dict[str, Any]] = []
    for competence, published in sorted(original.items()):
        if not isinstance(published, dict):
            raise ValueError(f"Métricas inválidas na baseline: {competence}")
        current_path = gold_dir / f"overview-{competence}.json"
        if not current_path.is_file():
            differences.append({
                "competence": competence,
                "error": "overview reconstruído ausente",
            })
            continue
        current = _read_json(current_path)
        changed = {
            key: {"published": previous, "reconstructed": current.get(key)}
            for key, previous in published.items()
            if current.get(key) != previous
        }
        if changed:
            differences.append({
                "competence": competence,
                "changed_metrics": changed,
            })
    return differences



def rehydrate_published_history(
    *, ingest_competence: str, baseline_path: Path
) -> dict[str, Any]:
    """Rebuild previous MOV/FOR/EXC without accepting changed historical sources."""
    baseline = _read_json(baseline_path)
    artifacts = baseline.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Snapshot publicado vazio ou inválido.")
    competencies = sorted(artifacts)
    if any(comp >= ingest_competence for comp in competencies):
        raise ValueError("Snapshot contém competência posterior ou igual à auditoria.")

    report_path = settings.gold_path / f"rehydration-{ingest_competence}.json"
    report: dict[str, Any] = {
        "version": 1,
        "ingest_competence": ingest_competence,
        "source": "FTP oficial do MTE, conferido contra manifests publicados",
        "published_competencies": competencies,
        "processed": [],
        "baseline_differences": [],
        "baseline_metric_differences": [],
        "passed": False,
    }

    try:
        for competence in competencies:
            expected = _expected_manifests(
                competence,
                bronze_root=settings.bronze_path,
                approvals_path=settings.publication_approvals_path,
            )
            archive_dir = settings.bronze_path / competence / "archives"
            extracted_dir = settings.bronze_path / competence / "extracted"
            try:
                downloads = download_month_resilient(
                    competence,
                    archive_dir,
                    file_types=KINDS,
                    official_only=True,
                )
                if sorted(item.kind for item in downloads) != sorted(KINDS):
                    raise ValueError(f"MOV/FOR/EXC incompletos: {competence}")
                if any(
                    item.transport != "ftp_mte"
                    or not item.url.startswith(OFFICIAL_PREFIX)
                    for item in downloads
                ):
                    raise ValueError(f"Origem não oficial: {competence}")
                write_download_manifest(
                    downloads, archive_dir / "download-manifest.json"
                )
                command_extract(competence)

                verified = {
                    kind: _verify_extracted(
                        competence,
                        kind=kind,
                        extracted_dir=extracted_dir,
                        original=expected[kind],
                    )
                    for kind in KINDS
                }
                command_transform(competence)
                for kind in ("FOR", "EXC"):
                    transform_adjustment_file(
                        verified[kind],
                        ingest_competence=competence,
                        kind=kind,
                        silver_dir=settings.silver_path,
                        gold_dir=settings.gold_path,
                        cbo_config_path=settings.cbo_config_path,
                    )
                report["processed"].append(
                    {
                        "competence": competence,
                        "verified_original_sha256": {
                            kind: expected[kind]["sha256"] for kind in KINDS
                        },
                    }
                )
            finally:
                # Never retain the raw TXT or 7z files, even when the audit fails.
                for path in extracted_dir.glob("*.txt"):
                    path.unlink()
                for path in archive_dir.glob("*.7z"):
                    path.unlink()

        # Recreate the existing historical series BEFORE applying the new FOR/EXC.
        # A mismatch cannot be attributed safely to the new competence.
        for competence in competencies:
            base = settings.silver_path / f"caged_tech_{competence}.parquet"
            if not base.is_file():
                raise FileNotFoundError(f"Silver histórico ausente: {competence}")
            build_gold(
                base,
                yearmonth=competence,
                gold_dir=settings.gold_path,
                ipca_cache_path=settings.ipca_cache_path,
                municipalities_cache_path=settings.municipalities_cache_path,
                population_cache_path=settings.population_cache_path,
            )

        differences = _compare_published_artifacts(baseline, settings.gold_path)
        report["baseline_differences"] = differences
        metrics = _compare_overview_metrics(baseline, settings.gold_path)
        report["baseline_metric_differences"] = metrics
        if differences or metrics:
            by_month: dict[str, list[str]] = {}
            for item in differences:
                by_month.setdefault(str(item["competence"]), []).append(
                    str(item["file"])
                )
            print(
                "DIAGNÓSTICO HISTÓRICO - publicação bloqueada:",
                json.dumps(
                    {
                        "arquivos_com_sha_diferente_por_competencia": by_month,
                        "indicadores_alterados": metrics,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )
            raise RuntimeError(
                "Reconstrução histórica diverge da baseline publicada; "
                "análise metodológica obrigatória antes da competência nova."
            )
        report["passed"] = True
        return report
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competence", help="Nova competência no formato AAAAMM")
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    if (
        len(args.competence) != 6
        or not args.competence.isdigit()
        or args.competence < "202609"
    ):
        parser.error("Somente auditorias de competência >= 202609.")
    result = rehydrate_published_history(
        ingest_competence=args.competence, baseline_path=args.baseline
    )
    print(
        "histórico oficial reconstituído: "
        f"competências={len(result['processed'])} baseline=identical"
    )


if __name__ == "__main__":
    main()
