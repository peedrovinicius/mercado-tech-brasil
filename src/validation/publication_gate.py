from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.validation.official_reference import reference_fingerprint


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
    reference_sha256: str | None
    generated_at_utc: str
    checks: tuple[GateCheck, ...]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    reference_sha256: str | None = None

    quality_path = gold_dir / f"quality-{yearmonth}.json"
    overview_path = gold_dir / f"overview-{yearmonth}.json"
    market_path = gold_dir / f"market-{yearmonth}.parquet"
    national_audit_path = gold_dir / f"audit-national-mov-{yearmonth}.json"
    municipality_path = gold_dir / f"by-municipality-{yearmonth}.json"

    for check_id, path in {
        "quality_report": quality_path,
        "overview": overview_path,
        "gold_market": market_path,
        "national_mov_audit": national_audit_path,
        "municipality_gold": municipality_path,
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


    if municipality_path.exists():
        municipality = _read_json(municipality_path)
        municipality_items = municipality.get("items")
        dimension_ok = isinstance(municipality_items, list) and bool(
            municipality_items
        )
        residual_count = 0
        if dimension_ok:
            for item in municipality_items:
                code = str(item.get("municipio_codigo_caged") or "")
                name = str(item.get("municipio_nome") or "")
                uf = str(item.get("uf") or "")
                ibge_code = item.get("municipio_codigo_ibge")

                if code == "999999":
                    residual_count += 1
                    if name != "Não identificado" or uf != "NI":
                        dimension_ok = False
                        break
                    continue

                if (
                    not code
                    or not name
                    or len(uf) != 2
                    or len(str(ibge_code or "")) != 7
                ):
                    dimension_ok = False
                    break

        checks.append(
            GateCheck(
                id="municipality_dimension_quality",
                passed=dimension_ok,
                message=(
                    "Dimensão municipal identificada e residual controlado: "
                    f"{len(municipality_items)} itens, "
                    f"{residual_count} residual."
                    if dimension_ok
                    else "Dimensão municipal possui item sem identificação válida."
                ),
            )
        )

        population_source = municipality.get("population_source")
        if population_source:
            population_year = municipality.get("population_reference_year")
            population_date = str(
                municipality.get("population_reference_date") or ""
            )
            population_url = str(
                municipality.get("population_source_url") or ""
            )
            population_published_at = str(
                municipality.get("population_published_at") or ""
            )
            population_sha = str(
                municipality.get("population_cache_sha256") or ""
            )
            metadata_ok = bool(
                isinstance(population_year, int)
                and population_year >= 2000
                and population_date == f"{population_year}-07-01"
                and population_url.startswith("https://")
                and len(population_published_at) == 10
                and len(population_sha) == 64
                and municipality.get("population_enrichment_status")
                == "complete"
            )
            checks.append(
                GateCheck(
                    id="municipality_population_metadata",
                    passed=metadata_ok,
                    message=(
                        "Referência populacional municipal possui proveniência completa."
                        if metadata_ok
                        else "Metadados da referência populacional estão incompletos."
                    ),
                )
            )

            population_coverage_ok = dimension_ok
            identified_count = 0
            if population_coverage_ok:
                for item in municipality_items:
                    code = str(item.get("municipio_codigo_caged") or "")
                    if code == "999999":
                        if any(
                            item.get(key) is not None
                            for key in (
                                "population_estimate",
                                "admissions_per_100k",
                                "dismissals_per_100k",
                                "balance_per_100k",
                            )
                        ):
                            population_coverage_ok = False
                            break
                        continue

                    identified_count += 1
                    raw_population = item.get("population_estimate")
                    if (
                        raw_population is None
                        or int(raw_population) <= 0
                        or item.get("population_reference_year")
                        != population_year
                    ):
                        population_coverage_ok = False
                        break

                    population_value = int(raw_population)
                    expected_rates = {
                        "admissions_per_100k": round(
                            int(item.get("admissions") or 0)
                            * 100000
                            / population_value,
                            4,
                        ),
                        "dismissals_per_100k": round(
                            int(item.get("dismissals") or 0)
                            * 100000
                            / population_value,
                            4,
                        ),
                        "balance_per_100k": round(
                            int(item.get("balance") or 0)
                            * 100000
                            / population_value,
                            4,
                        ),
                    }
                    if any(
                        item.get(key) != value
                        for key, value in expected_rates.items()
                    ):
                        population_coverage_ok = False
                        break

            checks.append(
                GateCheck(
                    id="municipality_population_coverage",
                    passed=population_coverage_ok,
                    message=(
                        "População e taxas por 100 mil validadas para "
                        f"{identified_count} municípios identificados."
                        if population_coverage_ok
                        else "Cobertura ou taxa populacional municipal é inválida."
                    ),
                )
            )

            population_report_path = (
                gold_dir / f"population-enrichment-{yearmonth}.json"
            )
            report_ok = False
            if population_report_path.exists():
                report = _read_json(population_report_path)
                report_ok = bool(
                    report.get("coverage_complete") is True
                    and int(report.get("population_year") or 0)
                    == population_year
                    and report.get("population_cache_sha256")
                    == population_sha
                    and report.get("municipality_artifact_sha256")
                    == _sha256(municipality_path)
                    and int(report.get("matched_population") or 0)
                    == identified_count
                    and int(report.get("missing_population") or -1) == 0
                )
            checks.append(
                GateCheck(
                    id="municipality_population_report",
                    passed=report_ok,
                    message=(
                        "Relatório de enriquecimento populacional confere com o Gold."
                        if report_ok
                        else "Relatório de enriquecimento populacional ausente ou divergente."
                    ),
                )
            )

    if reference_path.exists():
        reference = _read_json(reference_path).get(yearmonth)
        if reference:
            reference_sha256 = reference_fingerprint(reference)
            ref_adm = int(reference["admissoes"])
            ref_des = int(reference["desligamentos"])
            ref_balance = int(reference["saldo"])
            reference_integrity = ref_adm - ref_des == ref_balance
            checks.append(
                GateCheck(
                    id="official_reference_integrity",
                    passed=reference_integrity,
                    message="Referência oficial publicada é internamente consistente.",
                )
            )

            if national_audit_path.exists():
                audit = _read_json(national_audit_path)
                audit_adm = int(audit.get("admissions") or 0)
                audit_des = int(audit.get("dismissals") or 0)
                audit_balance = int(audit.get("balance") or 0)
                reconciliation_ok = (
                    audit_adm == ref_adm
                    and audit_des == ref_des
                    and audit_balance == ref_balance
                )
                checks.append(
                    GateCheck(
                        id="national_reference_reconciliation",
                        passed=reconciliation_ok,
                        message=(
                            "MOV nacional reconciliado exatamente com a referência oficial."
                            if reconciliation_ok
                            else (
                                "MOV nacional diverge da referência oficial: "
                                f"MOV={audit_adm}/{audit_des}/{audit_balance}; "
                                f"referência={ref_adm}/{ref_des}/{ref_balance}."
                            )
                        ),
                    )
                )

                ref_ni = reference.get("nao_identificado")
                if isinstance(ref_ni, dict):
                    audit_ni = audit.get("non_identified") or {}
                    ni_ok = (
                        int(audit_ni.get("admissions") or 0)
                        == int(ref_ni.get("admissoes") or 0)
                        and int(audit_ni.get("dismissals") or 0)
                        == int(ref_ni.get("desligamentos") or 0)
                        and int(audit_ni.get("balance") or 0)
                        == int(ref_ni.get("saldo") or 0)
                    )
                    checks.append(
                        GateCheck(
                            id="non_identified_reconciliation",
                            passed=ni_ok,
                            message=(
                                "Categoria Não identificado reconciliada com a referência oficial."
                                if ni_ok
                                else "Categoria Não identificado diverge da referência oficial."
                            ),
                        )
                    )
        else:
            checks.append(
                GateCheck(
                    id="official_reference_available",
                    passed=False,
                    message="Não há referência oficial registrada para a competência.",
                )
            )
    else:
        checks.append(
            GateCheck(
                id="official_reference_available",
                passed=False,
                message="Arquivo de referências oficiais não encontrado.",
            )
        )

    automatic_checks_passed = all(check.passed for check in checks if check.blocking)

    approval = _load_approval(approvals_path, yearmonth)
    approval_valid = bool(
        approval
        and approval.get("approved") is True
        and source_sha256
        and reference_sha256
        and approval.get("source_sha256") == source_sha256
        and approval.get("reference_sha256") == reference_sha256
    )
    checks.append(
        GateCheck(
            id="manual_methodology_approval",
            passed=approval_valid,
            message=(
                "Revisão metodológica aprovada e vinculada à origem e à referência atuais."
                if approval_valid
                else (
                    "Revisão metodológica pendente ou vinculada a outra origem "
                    "ou referência oficial."
                )
            ),
        )
    )

    return PublicationGateResult(
        competence=yearmonth,
        automatic_checks_passed=automatic_checks_passed,
        manual_approval_valid=approval_valid,
        publishable=automatic_checks_passed and approval_valid,
        source_sha256=source_sha256,
        reference_sha256=reference_sha256,
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
    reference_path: Path,
    approvals_path: Path,
) -> dict:
    manifest_result = _find_mov_manifest(bronze_dir, yearmonth)
    if manifest_result is None:
        raise FileNotFoundError("Manifesto MOV não encontrado para a competência.")

    _, manifest = manifest_result
    source_sha256 = manifest.get("sha256")
    if not source_sha256:
        raise ValueError("Manifesto MOV sem SHA-256.")

    references = _read_json(reference_path) if reference_path.exists() else {}
    reference = references.get(yearmonth)
    if not isinstance(reference, dict):
        raise FileNotFoundError(
            f"Referência oficial não encontrada para {yearmonth}."
        )
    reference_sha256 = reference_fingerprint(reference)

    approvals = _read_json(approvals_path) if approvals_path.exists() else {}
    approval = {
        "approved": True,
        "reviewer": reviewer,
        "notes": notes,
        "source_sha256": source_sha256,
        "reference_sha256": reference_sha256,
        "approved_at_utc": datetime.now(UTC).isoformat(),
    }
    approvals[yearmonth] = approval
    approvals_path.parent.mkdir(parents=True, exist_ok=True)
    approvals_path.write_text(
        json.dumps(approvals, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return approval
