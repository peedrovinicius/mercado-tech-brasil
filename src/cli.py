from __future__ import annotations

import argparse
from pathlib import Path

from src.core.settings import settings
from src.gold.aggregate import build_gold
from src.ingestion.archive import extract_7z
from src.ingestion.ftp_caged import download_month
from src.ingestion.local import ingest_local_file
from src.ingestion.manifest import build_manifest, write_manifest
from src.transform.caged import transform_mov_file
from src.validation.publication_gate import (
    approve_competence,
    evaluate_publication_gate,
    write_publication_gate,
)


def command_download(yearmonth: str) -> None:
    month_dir = settings.bronze_path / yearmonth
    archives = download_month(yearmonth, month_dir / "archives")
    for archive in archives:
        print(f"baixado: {archive}")


def command_extract(yearmonth: str) -> None:
    archive_dir = settings.bronze_path / yearmonth / "archives"
    extracted_dir = settings.bronze_path / yearmonth / "extracted"

    archives = sorted(archive_dir.glob("*.7z"))
    if not archives:
        raise SystemExit(f"Nenhum .7z em {archive_dir}")

    for archive in archives:
        extracted = extract_7z(archive, extracted_dir)
        for file in extracted:
            manifest = build_manifest(file, "novo_caged", yearmonth)
            write_manifest(
                manifest,
                file.with_suffix(file.suffix + ".manifest.json"),
            )
            print(f"extraído: {file}")


def _find_mov(yearmonth: str) -> Path:
    extracted_dir = settings.bronze_path / yearmonth / "extracted"
    candidates = [
        path
        for path in extracted_dir.rglob("*")
        if path.is_file()
        and "CAGEDMOV" in path.name.upper()
        and path.suffix.lower() == ".txt"
    ]
    if len(candidates) != 1:
        raise SystemExit(
            f"Esperado exatamente 1 TXT MOV em {extracted_dir}; encontrados: {len(candidates)}"
        )
    return candidates[0]


def command_transform(yearmonth: str) -> None:
    mov = _find_mov(yearmonth)
    result = transform_mov_file(
        mov,
        yearmonth=yearmonth,
        silver_dir=settings.silver_path,
        gold_dir=settings.gold_path,
        cbo_config_path=settings.cbo_config_path,
    )
    print(
        f"transformado: lidas={result.rows_read:,} "
        f"válidas={result.rows_valid:,} "
        f"rejeitadas={result.rows_rejected:,} "
        f"tech={result.rows_tech:,}"
    )


def command_gold(yearmonth: str) -> None:
    silver = settings.silver_path / f"caged_tech_{yearmonth}.parquet"
    if not silver.exists():
        raise SystemExit(f"Silver não encontrada: {silver}")
    parquet, overview = build_gold(
        silver,
        yearmonth=yearmonth,
        gold_dir=settings.gold_path,
    )
    print(f"gold: {parquet}")
    print(f"overview: {overview}")


def _run_publication_gate(
    yearmonth: str,
    *,
    min_valid_rate: float = 0.99,
    strict: bool = False,
) -> None:
    result = evaluate_publication_gate(
        yearmonth=yearmonth,
        bronze_dir=settings.bronze_path,
        gold_dir=settings.gold_path,
        reference_path=settings.reference_totals_path,
        approvals_path=settings.publication_approvals_path,
        min_valid_rate=min_valid_rate,
    )
    destination = settings.gold_path / f"publication-gate-{yearmonth}.json"
    write_publication_gate(result, destination)

    print(f"gate: {destination}")
    for check in result.checks:
        status = "PASS" if check.passed else ("WARN" if not check.blocking else "FAIL")
        print(f"[{status}] {check.id}: {check.message}")

    print(
        "publication: "
        + ("APPROVED" if result.publishable else "BLOCKED")
        + f" | automatic={result.automatic_checks_passed}"
        + f" | manual={result.manual_approval_valid}"
    )

    if strict and not result.publishable:
        raise SystemExit(2)


def command_pipeline(yearmonth: str) -> None:
    command_download(yearmonth)
    command_extract(yearmonth)
    command_transform(yearmonth)
    command_gold(yearmonth)
    _run_publication_gate(yearmonth)


def command_ingest_local(yearmonth: str, file_path: str, kind: str) -> None:
    result = ingest_local_file(
        Path(file_path).resolve(),
        yearmonth=yearmonth,
        kind=kind,
        bronze_root=settings.bronze_path,
    )
    print(f"bronze: {result.bronze_file}")
    for manifest in result.manifest_files:
        print(f"manifest: {manifest}")


def command_local_pipeline(yearmonth: str, file_path: str, kind: str) -> None:
    command_ingest_local(yearmonth, file_path, kind)
    if kind.upper() != "MOV":
        print(
            "Arquivo preservado na Bronze. "
            "FOR/EXC ainda não geram Silver/Gold automaticamente."
        )
        return
    command_transform(yearmonth)
    command_gold(yearmonth)
    _run_publication_gate(yearmonth)


def command_validate_release(
    yearmonth: str,
    *,
    min_valid_rate: float,
    strict: bool,
) -> None:
    _run_publication_gate(
        yearmonth,
        min_valid_rate=min_valid_rate,
        strict=strict,
    )


def command_approve_release(
    yearmonth: str,
    *,
    reviewer: str,
    notes: str,
    acknowledged: bool,
) -> None:
    if not acknowledged:
        raise SystemExit(
            "A aprovação exige --acknowledge-methodology-reviewed após revisar "
            "layout, rejeições e metodologia."
        )

    approval = approve_competence(
        yearmonth=yearmonth,
        reviewer=reviewer,
        notes=notes,
        bronze_dir=settings.bronze_path,
        approvals_path=settings.publication_approvals_path,
    )
    print(
        f"aprovação registrada: reviewer={approval['reviewer']} "
        f"sha256={approval['source_sha256']}"
    )
    _run_publication_gate(yearmonth)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mercado-tech-brasil")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("download", "extract", "transform", "gold", "pipeline"):
        item = sub.add_parser(name)
        item.add_argument("yearmonth", help="Competência AAAAMM, ex.: 202607")

    ingest = sub.add_parser(
        "ingest-local",
        help="Ingere TXT ou .7z oficial já disponível no computador.",
    )
    ingest.add_argument("yearmonth", help="Competência AAAAMM, ex.: 202607")
    ingest.add_argument("file", help="Caminho do arquivo TXT ou .7z")
    ingest.add_argument("--kind", choices=["MOV", "FOR", "EXC"], default="MOV")

    local_pipeline = sub.add_parser(
        "local-pipeline",
        help="Ingere arquivo local e, para MOV, gera Silver e Gold.",
    )
    local_pipeline.add_argument("yearmonth", help="Competência AAAAMM")
    local_pipeline.add_argument("file", help="Caminho do arquivo TXT ou .7z")
    local_pipeline.add_argument("--kind", choices=["MOV", "FOR", "EXC"], default="MOV")

    validate = sub.add_parser(
        "validate-release",
        help="Executa o gate de publicação de uma competência.",
    )
    validate.add_argument("yearmonth", help="Competência AAAAMM")
    validate.add_argument("--min-valid-rate", type=float, default=0.99)
    validate.add_argument(
        "--strict",
        action="store_true",
        help="Retorna código 2 enquanto a competência não estiver publicável.",
    )

    approve = sub.add_parser(
        "approve-release",
        help="Registra revisão metodológica vinculada ao SHA-256 do MOV atual.",
    )
    approve.add_argument("yearmonth", help="Competência AAAAMM")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--notes", required=True)
    approve.add_argument(
        "--acknowledge-methodology-reviewed",
        action="store_true",
        help="Confirma que layout, rejeições e metodologia foram revisados.",
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "ingest-local":
        command_ingest_local(args.yearmonth, args.file, args.kind)
        return

    if args.command == "local-pipeline":
        command_local_pipeline(args.yearmonth, args.file, args.kind)
        return

    if args.command == "validate-release":
        command_validate_release(
            args.yearmonth,
            min_valid_rate=args.min_valid_rate,
            strict=args.strict,
        )
        return

    if args.command == "approve-release":
        command_approve_release(
            args.yearmonth,
            reviewer=args.reviewer,
            notes=args.notes,
            acknowledged=args.acknowledge_methodology_reviewed,
        )
        return

    commands = {
        "download": command_download,
        "extract": command_extract,
        "transform": command_transform,
        "gold": command_gold,
        "pipeline": command_pipeline,
    }
    commands[args.command](args.yearmonth)


if __name__ == "__main__":
    main()
