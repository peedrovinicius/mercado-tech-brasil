from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class RaisGateCheck:
    id: str
    passed: bool
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class RaisPublicationGateResult:
    year: int
    automatic_checks_passed: bool
    manual_approval_valid: bool
    publishable: bool
    release_sha256: str | None
    generated_at_utc: str
    checks: tuple[RaisGateCheck, ...]


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_hashes(bronze_dir: Path, year: int) -> list[str]:
    manifest_path = (
        bronze_dir / "rais" / str(year) / "archives" / "download-manifest.json"
    )
    if not manifest_path.exists():
        return []

    payload = _read_json(manifest_path)
    hashes = []
    for item in payload.get("files", []):
        if not isinstance(item, dict):
            continue
        sha256 = str(item.get("sha256") or "").strip().lower()
        if len(sha256) == 64:
            hashes.append(sha256)
    return sorted(set(hashes))


def _release_artifacts(gold_dir: Path, silver_dir: Path, year: int) -> list[Path]:
    return [
        silver_dir / f"rais_reconciliation_{year}.json",
        gold_dir / f"rais-overview-{year}.json",
        gold_dir / f"rais-by-uf-{year}.json",
        gold_dir / f"rais-by-cbo-family-{year}.json",
        gold_dir / f"rais-market-{year}.parquet",
    ]


def build_rais_release_sha256(
    *,
    bronze_dir: Path,
    silver_dir: Path,
    gold_dir: Path,
    year: int,
) -> str | None:
    source_hashes = _source_hashes(bronze_dir, year)
    artifacts = _release_artifacts(gold_dir, silver_dir, year)

    if not source_hashes or any(not path.exists() for path in artifacts):
        return None

    digest = hashlib.sha256()
    digest.update(f"rais-release:{year}\n".encode("utf-8"))

    for sha256 in source_hashes:
        digest.update(f"source:{sha256}\n".encode("utf-8"))

    for path in artifacts:
        digest.update(f"artifact:{path.name}:{_sha256_file(path)}\n".encode("utf-8"))

    return digest.hexdigest()


def _load_approval(approvals_path: Path, year: int) -> dict | None:
    if not approvals_path.exists():
        return None
    payload = _read_json(approvals_path)
    approval = payload.get(str(year))
    return approval if isinstance(approval, dict) else None


def evaluate_rais_publication_gate(
    *,
    year: int,
    bronze_dir: Path,
    silver_dir: Path,
    gold_dir: Path,
    approvals_path: Path,
) -> RaisPublicationGateResult:
    checks: list[RaisGateCheck] = []

    source_hashes = _source_hashes(bronze_dir, year)
    checks.append(
        RaisGateCheck(
            id="source_provenance",
            passed=bool(source_hashes),
            message=(
                f"Proveniência RAIS registrada para {len(source_hashes)} arquivo(s) de origem."
                if source_hashes
                else "Manifesto anual RAIS sem SHA-256 de origem."
            ),
        )
    )

    reconciliation_path = silver_dir / f"rais_reconciliation_{year}.json"
    overview_path = gold_dir / f"rais-overview-{year}.json"
    by_uf_path = gold_dir / f"rais-by-uf-{year}.json"
    by_family_path = gold_dir / f"rais-by-cbo-family-{year}.json"
    market_path = gold_dir / f"rais-market-{year}.parquet"

    required = {
        "reconciliation": reconciliation_path,
        "overview": overview_path,
        "by_uf": by_uf_path,
        "by_cbo_family": by_family_path,
        "market": market_path,
    }
    for check_id, path in required.items():
        checks.append(
            RaisGateCheck(
                id=f"artifact_{check_id}",
                passed=path.exists(),
                message=(
                    f"Artefato encontrado: {path.name}"
                    if path.exists()
                    else f"Artefato ausente: {path.name}"
                ),
            )
        )

    reconciliation: dict = {}
    if reconciliation_path.exists():
        reconciliation = _read_json(reconciliation_path)
        reconciliation_ok = (
            int(reconciliation.get("year") or 0) == year
            and reconciliation.get("reconciled") is True
            and reconciliation.get("gold_ready") is True
            and int(reconciliation.get("difference") or 0) == 0
        )
        checks.append(
            RaisGateCheck(
                id="exact_national_reconciliation",
                passed=reconciliation_ok,
                message=(
                    "Estoque nacional RAIS reconciliado exatamente com a referência oficial."
                    if reconciliation_ok
                    else "Reconciliação nacional RAIS não está aprovada ou possui diferença."
                ),
            )
        )

    overview: dict = {}
    if overview_path.exists():
        overview = _read_json(overview_path)
        overview_year_ok = int(overview.get("year") or 0) == year
        checks.append(
            RaisGateCheck(
                id="overview_year",
                passed=overview_year_ok,
                message=(
                    "Ano do overview RAIS confere."
                    if overview_year_ok
                    else "Ano do overview RAIS diverge."
                ),
            )
        )

        tech_stock = int(overview.get("active_stock_tech") or 0)
        national_stock = int(
            overview.get("active_stock_national_reference") or 0
        )
        reference_stock = int(reconciliation.get("expected_active") or 0)
        stock_ok = (
            tech_stock >= 0
            and national_stock > 0
            and national_stock == reference_stock
            and tech_stock <= national_stock
        )
        checks.append(
            RaisGateCheck(
                id="overview_stock_integrity",
                passed=stock_ok,
                message=(
                    f"Estoque tech={tech_stock:,}; nacional={national_stock:,}."
                    if stock_ok
                    else "Totais do overview RAIS não fecham com a reconciliação."
                ),
            )
        )

        publication_flag_ok = overview.get("publication_ready") is False
        checks.append(
            RaisGateCheck(
                id="pre_gate_publication_block",
                passed=publication_flag_ok,
                message=(
                    "Gold permanece bloqueado antes do gate final."
                    if publication_flag_ok
                    else "Gold foi marcado como publicável antes do gate final."
                ),
            )
        )

    if by_uf_path.exists() and overview:
        payload = _read_json(by_uf_path)
        items = payload.get("items")
        total = (
            sum(int(item.get("active_stock") or 0) for item in items)
            if isinstance(items, list)
            else -1
        )
        expected = int(overview.get("active_stock_tech") or 0)
        checks.append(
            RaisGateCheck(
                id="uf_total",
                passed=total == expected,
                message=(
                    f"Agregado por UF fecha o estoque tech: {total:,}."
                    if total == expected
                    else f"Agregado por UF={total:,}; overview={expected:,}."
                ),
            )
        )

    if by_family_path.exists() and overview:
        payload = _read_json(by_family_path)
        items = payload.get("items")
        total = (
            sum(int(item.get("active_stock") or 0) for item in items)
            if isinstance(items, list)
            else -1
        )
        expected = int(overview.get("active_stock_tech") or 0)
        checks.append(
            RaisGateCheck(
                id="cbo_family_total",
                passed=total == expected,
                message=(
                    f"Agregado por família CBO fecha o estoque tech: {total:,}."
                    if total == expected
                    else f"Famílias CBO={total:,}; overview={expected:,}."
                ),
            )
        )

    if market_path.exists() and overview:
        import pyarrow.parquet as pq

        table = pq.read_table(market_path, columns=["active_stock"])
        total = sum(int(value or 0) for value in table["active_stock"].to_pylist())
        expected = int(overview.get("active_stock_tech") or 0)
        checks.append(
            RaisGateCheck(
                id="market_total",
                passed=total == expected,
                message=(
                    f"Parquet Gold fecha o estoque tech: {total:,}."
                    if total == expected
                    else f"Parquet Gold={total:,}; overview={expected:,}."
                ),
            )
        )

    release_sha256 = build_rais_release_sha256(
        bronze_dir=bronze_dir,
        silver_dir=silver_dir,
        gold_dir=gold_dir,
        year=year,
    )
    checks.append(
        RaisGateCheck(
            id="release_fingerprint",
            passed=bool(release_sha256),
            message=(
                f"Fingerprint da release: {release_sha256}."
                if release_sha256
                else "Fingerprint da release não pôde ser calculado."
            ),
        )
    )

    automatic_checks_passed = all(
        check.passed for check in checks if check.blocking
    )

    approval = _load_approval(approvals_path, year)
    approval_valid = bool(
        approval
        and approval.get("approved") is True
        and release_sha256
        and approval.get("release_sha256") == release_sha256
    )
    checks.append(
        RaisGateCheck(
            id="manual_methodology_approval",
            passed=approval_valid,
            message=(
                "Revisão metodológica RAIS aprovada e vinculada ao fingerprint atual."
                if approval_valid
                else "Revisão metodológica RAIS pendente ou vinculada a outra release."
            ),
        )
    )

    return RaisPublicationGateResult(
        year=year,
        automatic_checks_passed=automatic_checks_passed,
        manual_approval_valid=approval_valid,
        publishable=automatic_checks_passed and approval_valid,
        release_sha256=release_sha256,
        generated_at_utc=datetime.now(UTC).isoformat(),
        checks=tuple(checks),
    )


def write_rais_publication_gate(
    result: RaisPublicationGateResult,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["checks"] = [asdict(check) for check in result.checks]
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def approve_rais_release(
    *,
    year: int,
    reviewer: str,
    notes: str,
    bronze_dir: Path,
    silver_dir: Path,
    gold_dir: Path,
    approvals_path: Path,
) -> dict:
    release_sha256 = build_rais_release_sha256(
        bronze_dir=bronze_dir,
        silver_dir=silver_dir,
        gold_dir=gold_dir,
        year=year,
    )
    if not release_sha256:
        raise ValueError(
            "Não foi possível calcular o fingerprint da release RAIS."
        )

    approvals = _read_json(approvals_path) if approvals_path.exists() else {}
    approval = {
        "approved": True,
        "reviewer": reviewer,
        "notes": notes,
        "release_sha256": release_sha256,
        "approved_at_utc": datetime.now(UTC).isoformat(),
    }
    approvals[str(year)] = approval
    approvals_path.parent.mkdir(parents=True, exist_ok=True)
    approvals_path.write_text(
        json.dumps(approvals, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return approval
