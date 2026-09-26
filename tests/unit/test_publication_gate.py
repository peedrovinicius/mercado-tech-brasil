import json
from pathlib import Path

from src.validation.publication_gate import approve_competence, evaluate_publication_gate


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    bronze = tmp_path / "bronze"
    gold = tmp_path / "gold"
    reference = tmp_path / "reference.json"
    approvals = tmp_path / "approvals.json"

    _write_json(
        bronze / "202607" / "extracted" / "CAGEDMOV.txt.manifest.json",
        {
            "source": "novo_caged_mov_local",
            "competence": "202607",
            "original_name": "CAGEDMOV202607.txt",
            "sha256": "abc123",
            "ingested_at_utc": "2026-09-25T20:00:00+00:00",
        },
    )
    _write_json(
        gold / "quality-202607.json",
        {
            "competence": "202607",
            "rows_read": 1000,
            "rows_valid": 999,
            "rows_rejected": 1,
            "valid_rate": 0.999,
        },
    )
    _write_json(
        gold / "overview-202607.json",
        {
            "competence": "202607",
            "admissions": 60,
            "dismissals": 40,
            "balance": 20,
        },
    )
    (gold / "market-202607.parquet").write_bytes(b"parquet-placeholder")
    _write_json(
        gold / "by-municipality-202607.json",
        {
            "competence": "202607",
            "items": [
                {
                    "municipio_codigo_caged": "230440",
                    "municipio_codigo_ibge": "2304400",
                    "municipio_nome": "Fortaleza",
                    "uf": "CE",
                    "admissions": 10,
                    "dismissals": 5,
                    "balance": 5,
                }
            ],
        },
    )
    _write_json(
        gold / "audit-national-mov-202607.json",
        {
            "competence": "202607",
            "admissions": 2262888,
            "dismissals": 2204320,
            "balance": 58568,
            "non_identified": {
                "admissions": 803,
                "dismissals": 566,
                "balance": 237,
            },
        },
    )
    _write_json(
        reference,
        {
            "202607": {
                "admissoes": 2262888,
                "desligamentos": 2204320,
                "saldo": 58568,
                "nao_identificado": {
                    "admissoes": 803,
                    "desligamentos": 566,
                    "saldo": 237,
                },
            }
        },
    )
    _write_json(approvals, {})
    return bronze, gold, reference, approvals


def test_gate_blocks_without_manual_approval(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )
    assert result.automatic_checks_passed is True
    assert result.manual_approval_valid is False
    assert result.publishable is False


def test_gate_publishes_after_sha_bound_approval(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    approve_competence(
        yearmonth="202607",
        reviewer="Pedro",
        notes="Layout, rejeições e metodologia revisados.",
        bronze_dir=bronze,
        approvals_path=approvals,
    )
    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )
    assert result.automatic_checks_passed is True
    assert result.manual_approval_valid is True
    assert result.publishable is True


def test_gate_invalidates_approval_when_source_sha_changes(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    approve_competence(
        yearmonth="202607",
        reviewer="Pedro",
        notes="Revisado.",
        bronze_dir=bronze,
        approvals_path=approvals,
    )
    manifest = bronze / "202607" / "extracted" / "CAGEDMOV.txt.manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["sha256"] = "different-sha"
    _write_json(manifest, payload)

    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )
    assert result.manual_approval_valid is False
    assert result.publishable is False


def test_gate_detects_overview_arithmetic_error(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    _write_json(
        gold / "overview-202607.json",
        {
            "competence": "202607",
            "admissions": 60,
            "dismissals": 40,
            "balance": 99,
        },
    )
    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )
    assert result.automatic_checks_passed is False
    assert any(check.id == "overview_arithmetic" and not check.passed for check in result.checks)


def test_gate_blocks_when_national_reference_diverges(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    audit_path = gold / "audit-national-mov-202607.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["admissions"] += 1
    _write_json(audit_path, audit)

    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is False
    assert any(
        check.id == "national_reference_reconciliation" and not check.passed
        for check in result.checks
    )


def test_gate_blocks_without_official_reference(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    _write_json(reference, {})

    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is False
    assert any(
        check.id == "official_reference_available" and not check.passed
        for check in result.checks
    )


def test_gate_blocks_invalid_municipality_dimension(tmp_path: Path):
    bronze, gold, reference, approvals = _fixture(tmp_path)
    _write_json(
        gold / "by-municipality-202607.json",
        {
            "competence": "202607",
            "items": [
                {
                    "municipio_codigo_caged": "999999",
                    "municipio_codigo_ibge": None,
                    "municipio_nome": None,
                    "uf": "NI",
                    "admissions": 2,
                    "dismissals": 0,
                    "balance": 2,
                }
            ],
        },
    )

    result = evaluate_publication_gate(
        yearmonth="202607",
        bronze_dir=bronze,
        gold_dir=gold,
        reference_path=reference,
        approvals_path=approvals,
    )

    assert result.automatic_checks_passed is False
    assert any(
        check.id == "municipality_dimension_quality" and not check.passed
        for check in result.checks
    )
