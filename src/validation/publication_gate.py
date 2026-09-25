from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class GateCheck:
    id: str
    passed: bool
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class PublicationGateResult:
    competence: str
    automatic_checks_passed: bool
    manual_approval_valid: bool
    publishable: bool
    source_sha256: str | None
    generated_at_utc: str
    checks: tuple[GateCheck, ...]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_mov_manifest(bronze_dir: Path, yearmonth: str) -> tuple[Path, dict] | None:
    month_dir = bronze_dir / yearmonth
    if not month_dir.exists():
        return None

    candidates: list[tuple[Path, dict]] = []
    for path in month_dir.rglob("*.manifest.json"):
        payload = _read_json(path)
        original_name = str(payload.get("original_name", "")).upper()
        source = str(payload.get("source", "")).lower()
        if "CAGEDMOV" in original_name or "_mov" in source:
            candidates.append((path, payload))

    if not candidates:
        return None

    candidates.sort(key=lambda item: str(item[1].get("ingested_at_utc", "")))
    return candidates[-1]


def _load_approval(approvals_path: Path, yearmonth: str) -> dict | None:
    if not approvals_path.exists():
        return None
    return _read_json(approvals_path).get(yearmonth)


def evaluate_publication_gate(
    *,
    yearmonth: str,
    bronze_dir: Path,
    gold_dir: Path,
    reference_path: Path,
    approvals_path: Path,
    min_valid_rate: float = 0.99,
) -> PublicationGateResult:
    checks: list[GateCheck] = []

    quality_path = gold_dir / f"quality-{yearmonth}.json"
    overview_path = gold_dir / f"overview-{yearmonth}.json"
    market_path = gold_dir / f"market-{yearmonth}.parquet"

    for check_id, path in {
        "quality_report": quality_path,
        "overview": overview_path,
        "gold_market": market_path,
    }.items():
        checks.append(
            GateCheck(
                id=check_id,
                passed=path.exists(),
                message=(
                    f"Artefato encontrado: {path.name}"
                    if path.exists()
                    else f"Artefato ausente: {path.name}"
                ),
            )
        )

    manifest_result = _find_mov_manifest(bronze_dir, yearmonth)
    source_sha256: str | None = None
    if manifest_result is None:
        checks.append(
            GateCheck(
                id="mov_provenance",
                passed=False,
                message="Manifesto do arquivo MOV não encontrado na Bronze.",
            )
        )
    else:
        _, manifest = manifest_result
        source_sha256 = str(manifest.get("sha256") or "") or None
        checks.append(
            GateCheck(
                id="mov_provenance",
                passed=bool(source_sha256),
                message=(
                    f"Proveniência MOV registrada com SHA-256 {source_sha256}."
                    if source_sha256
                    else "Manifesto MOV existe, mas não possui SHA-256."
                ),
            )
        )

    if quality_path.exists():
        quality = _read_json(quality_path)
        competence_ok = str(quality.get("competence")) == yearmonth
        checks.append(
            GateCheck(
                id="quality_competence",
                passed=competence_ok,
                message=(
                    "Competência do relatório de qualidade confere."
                    if competence_ok
                    else "Competência do relatório de qualidade diverge."
                ),
            )
        )

        rows_read = int(quality.get("rows_read") or 0)
        rows_valid = int(quality.get("rows_valid") or 0)
        rows_rejected = int(quality.get("rows_rejected") or 0)
        counts_ok = (
            rows_read > 0
            and 0 <= rows_valid <= rows_read
            and 0 <= rows_rejected <= rows_read
        )
        checks.append(
            GateCheck(
                id="quality_counts",
                passed=counts_ok,
                message=(
                    f"Contagens coerentes: lidas={rows_read}, válidas={rows_valid}, "
                    f"rejeitadas={rows_rejected}."
                    if counts_ok
                    else "Contagens do relatório de qualidade são inválidas."
                ),
            )
        )

        valid_rate = float(quality.get("valid_rate") or 0)
        checks.append(
            GateCheck(
                id="valid_rate",
                passed=valid_rate >= min_valid_rate,
                message=f"Taxa válida={valid_rate:.4%}; mínimo={min_valid_rate:.2%}.",
            )
        )

    if overview_path.exists():
        overview = _read_json(overview_path)
        competence_ok = str(overview.get("competence")) == yearmonth
        checks.append(
            GateCheck(
                id="overview_competence",
                passed=competence_ok,
                message=(
                    "Competência do overview confere."
                    if competence_ok
                    else "Competência do overview diverge."
                ),
            )
        )

        admissions = int(overview.get("admissions") or 0)
        dismissals = int(overview.get("dismissals") or 0)
        balance = int(overview.get("balance") or 0)
        arithmetic_ok = admissions - dismissals == balance
        checks.append(
            GateCheck(
                id="overview_arithmetic",
                passed=arithmetic_ok,
                message=(
                    f"Saldo confere: {admissions} - {dismissals} = {balance}."
                    if arithmetic_ok
                    else "Saldo do overview não é igual a admissões menos desligamentos."
                ),
            )
        )

    if reference_path.exists():
        reference = _read_json(reference_path).get(yearmonth)
        if reference:
            ref_adm = int(reference["admissoes"])
            ref_des = int(reference["desligamentos"])
            ref_balance = int(reference["saldo"])
            checks.append(
                GateCheck(
                    id="official_reference_integrity",
                    passed=ref_adm - ref_des == ref_balance,
                    message=(
                        "Referência oficial publicada é internamente consistente. "
                        "Ela não é comparada numericamente ao recorte tech MOV isolado."
                    ),
                )
            )
        else:
            checks.append(
                GateCheck(
                    id="official_reference_available",
                    passed=False,
                    message="Não há referência oficial registrada para a competência.",
                    blocking=False,
                )
            )

    automatic_checks_passed = all(check.passed for check in checks if check.blocking)

    approval = _load_approval(approvals_path, yearmonth)
    approval_valid = bool(
        approval
        and approval.get("approved") is True
        and source_sha256
        and approval.get("source_sha256") == source_sha256
    )
    checks.append(
        GateCheck(
            id="manual_methodology_approval",
            passed=approval_valid,
            message=(
                "Revisão metodológica aprovada e vinculada ao SHA-256 atual."
                if approval_valid
                else "Revisão metodológica pendente ou vinculada a outro SHA-256."
            ),
        )
    )

    return PublicationGateResult(
        competence=yearmonth,
        automatic_checks_passed=automatic_checks_passed,
        manual_approval_valid=approval_valid,
        publishable=automatic_checks_passed and approval_valid,
        source_sha256=source_sha256,
        generated_at_utc=datetime.now(UTC).isoformat(),
        checks=tuple(checks),
    )


def write_publication_gate(result: PublicationGateResult, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    payload["checks"] = [asdict(item) for item in result.checks]
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def approve_competence(
    *,
    yearmonth: str,
    reviewer: str,
    notes: str,
    bronze_dir: Path,
    approvals_path: Path,
) -> dict:
    manifest_result = _find_mov_manifest(bronze_dir, yearmonth)
    if manifest_result is None:
        raise FileNotFoundError("Manifesto MOV não encontrado para a competência.")

    _, manifest = manifest_result
    source_sha256 = manifest.get("sha256")
    if not source_sha256:
        raise ValueError("Manifesto MOV sem SHA-256.")

    approvals = _read_json(approvals_path) if approvals_path.exists() else {}
    approval = {
        "approved": True,
        "reviewer": reviewer,
        "notes": notes,
        "source_sha256": source_sha256,
        "approved_at_utc": datetime.now(UTC).isoformat(),
    }
    approvals[yearmonth] = approval
    approvals_path.parent.mkdir(parents=True, exist_ok=True)
    approvals_path.write_text(
        json.dumps(approvals, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return approval
