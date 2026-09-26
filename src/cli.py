from __future__ import annotations

import argparse
from pathlib import Path

from src.core.settings import settings
from src.db.loader import ReleaseNotApprovedError, load_approved_release
from src.gold.aggregate import build_gold
from src.ingestion.archive import extract_7z
from src.ingestion.https_caged import (
    download_month_resilient,
    write_download_manifest,
)
from src.ingestion.local import ingest_local_file
from src.ingestion.manifest import build_manifest, write_manifest
from src.ingestion.rais import (
    discover_files as discover_rais_files,
    download_year as download_rais_year,
    extract_year as extract_rais_year,
    write_download_manifest as write_rais_download_manifest,
)
from src.reference.ipca import fetch_ipca_indices, save_ipca_cache
from src.reference.municipalities import (
    fetch_municipalities,
    save_municipalities,
)
from src.reference.population import (
    fetch_population_estimates,
    save_population_cache,
)
from src.transform.adjustments import transform_adjustment_file
from src.transform.caged import transform_mov_file
from src.transform.rais_profile import profile_rais_values
from src.transform.rais_schema import inspect_rais_directory
from src.transform.rais_semantics import validate_layout_semantics
from src.transform.rais_silver import transform_rais_year
from src.transform.rais_value_semantics import validate_value_semantics
from src.validation.publication_gate import (
    approve_competence,
    evaluate_publication_gate,
    write_publication_gate,
)


def command_download(yearmonth: str) -> None:
    month_dir = settings.bronze_path / yearmonth
    archive_dir = month_dir / "archives"
    artifacts = download_month_resilient(yearmonth, archive_dir)
    write_download_manifest(
        artifacts,
        archive_dir / "download-manifest.json",
    )
    for artifact in artifacts:
        print(
            f"baixado: {artifact.path} "
            f"kind={artifact.kind} transport={artifact.transport}"
        )


def command_extract(yearmonth: str) -> None:
    import json

    archive_dir = settings.bronze_path / yearmonth / "archives"
    extracted_dir = settings.bronze_path / yearmonth / "extracted"

    archives = sorted(archive_dir.glob("*.7z"))
    if not archives:
        raise SystemExit(f"Nenhum .7z em {archive_dir}")

    download_manifest_path = archive_dir / "download-manifest.json"
    download_metadata: dict[str, dict[str, str]] = {}
    if download_manifest_path.exists():
        payload = json.loads(download_manifest_path.read_text(encoding="utf-8"))
        download_metadata = {
            str(item["path"]): item
            for item in payload.get("files", [])
        }

    for archive in archives:
        metadata = download_metadata.get(archive.name, {})
        extracted = extract_7z(archive, extracted_dir)
        for file in extracted:
            manifest = build_manifest(
                file,
                "novo_caged_mte",
                yearmonth,
                transport=metadata.get("transport"),
                source_url=metadata.get("url"),
            )
            write_manifest(
                manifest,
                file.with_suffix(file.suffix + ".manifest.json"),
            )
            print(f"extraído: {file}")


def _find_kind(yearmonth: str, kind: str) -> Path:
    extracted_dir = settings.bronze_path / yearmonth / "extracted"
    marker = f"CAGED{kind.upper()}"
    candidates = [
        path
        for path in extracted_dir.rglob("*")
        if path.is_file()
        and marker in path.name.upper()
        and path.suffix.lower() == ".txt"
    ]
    if len(candidates) != 1:
        raise SystemExit(
            f"Esperado exatamente 1 TXT {kind.upper()} em {extracted_dir}; "
            f"encontrados: {len(candidates)}"
        )
    return candidates[0]


def _find_mov(yearmonth: str) -> Path:
    return _find_kind(yearmonth, "MOV")


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


def _rebuild_affected_gold(adjustment_path: Path) -> None:
    try:
        import polars as pl
    except ImportError as exc:
        raise RuntimeError("Polars não está instalado.") from exc

    frame = pl.read_parquet(adjustment_path)
    if "effective_competence" not in frame.columns:
        return

    competencies = sorted(
        str(value)
        for value in frame["effective_competence"].drop_nulls().unique().to_list()
    )
    for competence in competencies:
        base = settings.silver_path / f"caged_tech_{competence}.parquet"
        if not base.exists():
            print(
                f"ajuste preservado: competência base {competence} "
                "ainda não foi ingerida"
            )
            continue
        build_gold(
            base,
            yearmonth=competence,
            gold_dir=settings.gold_path,
            ipca_cache_path=settings.ipca_cache_path,
            municipalities_cache_path=settings.municipalities_cache_path,
            population_cache_path=settings.population_cache_path,
        )
        print(f"gold reconstruído com ajustes: {competence}")


def command_transform_adjustment(yearmonth: str, kind: str) -> None:
    source = _find_kind(yearmonth, kind)
    result = transform_adjustment_file(
        source,
        ingest_competence=yearmonth,
        kind=kind,
        silver_dir=settings.silver_path,
        gold_dir=settings.gold_path,
        cbo_config_path=settings.cbo_config_path,
    )
    print(
        f"ajuste {kind}: lidas={result.rows_read:,} "
        f"válidas={result.rows_valid:,} "
        f"rejeitadas={result.rows_rejected:,} "
        f"tech={result.rows_tech:,}"
    )
    _rebuild_affected_gold(result.silver_path)


def command_gold(yearmonth: str) -> None:
    silver = settings.silver_path / f"caged_tech_{yearmonth}.parquet"
    if not silver.exists():
        raise SystemExit(f"Silver não encontrada: {silver}")
    parquet, overview = build_gold(
        silver,
        yearmonth=yearmonth,
        gold_dir=settings.gold_path,
        ipca_cache_path=settings.ipca_cache_path,
        municipalities_cache_path=settings.municipalities_cache_path,
        population_cache_path=settings.population_cache_path,
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
    for kind in ("FOR", "EXC"):
        try:
            command_transform_adjustment(yearmonth, kind)
        except SystemExit:
            print(f"ajuste {kind}: arquivo não disponível para {yearmonth}")
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
    normalized = kind.upper()
    if normalized == "MOV":
        command_transform(yearmonth)
        command_gold(yearmonth)
        _run_publication_gate(yearmonth)
        return

    command_transform_adjustment(yearmonth, normalized)


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


def command_rais_discover(year: int, dataset: str) -> None:
    files = discover_rais_files(year, dataset=dataset)
    if not files:
        raise SystemExit(
            f"Nenhum arquivo RAIS {dataset} encontrado para {year}."
        )

    for item in files:
        print(
            f"rais: ano={item.year} dataset={item.dataset} "
            f"arquivo={item.filename}"
        )


def command_rais_download(year: int, dataset: str) -> None:
    archive_dir = (
        settings.bronze_path
        / "rais"
        / str(year)
        / "archives"
    )
    files = download_rais_year(
        year,
        archive_dir,
        dataset=dataset,
    )
    manifest = archive_dir / "download-manifest.json"
    write_rais_download_manifest(
        year,
        files,
        manifest,
        dataset=dataset,
    )
    print(
        f"rais: {len(files)} arquivos baixados para {archive_dir} "
        f"dataset={dataset}"
    )
    print(f"rais manifest: {manifest}")


def command_rais_extract(year: int) -> None:
    base_dir = settings.bronze_path / "rais" / str(year)
    archive_dir = base_dir / "archives"
    extracted_dir = base_dir / "extracted"

    files = extract_rais_year(
        year,
        archive_dir,
        extracted_dir,
    )
    print(
        f"rais: {len(files)} arquivos extraídos para {extracted_dir}"
    )


def command_rais_inspect(year: int) -> None:
    base_dir = settings.bronze_path / "rais" / str(year)
    extracted_dir = base_dir / "extracted"
    report_path = base_dir / "layout-report.json"

    payload = inspect_rais_directory(
        extracted_dir,
        year=year,
        destination=report_path,
    )
    print(
        f"rais layout: arquivos={payload['files_inspected']} "
        f"layouts={payload['unique_layouts']} "
        f"relatório={report_path}"
    )
    print("rais publication: BLOCKED until semantic layout validation")


def command_rais_validate_layout(year: int) -> None:
    base_dir = settings.bronze_path / "rais" / str(year)
    layout_report = base_dir / "layout-report.json"
    destination = base_dir / "semantic-layout-report.json"

    if not layout_report.exists():
        raise SystemExit(
            f"Relatório de layout ausente: {layout_report}. "
            "Execute rais-inspect primeiro."
        )

    payload = validate_layout_semantics(
        layout_report,
        settings.root / "config" / "rais_semantic_contract.yml",
        destination,
    )
    status = "READY" if payload["silver_ready"] else "BLOCKED"
    print(
        f"rais semantic: status={status} "
        f"arquivos={payload['files_validated']} relatório={destination}"
    )
    if not payload["silver_ready"]:
        raise SystemExit(2)


def command_rais_profile_values(
    year: int,
    *,
    max_rows_per_file: int,
) -> None:
    base_dir = settings.bronze_path / "rais" / str(year)
    extracted_dir = base_dir / "extracted"
    layout_report = base_dir / "layout-report.json"
    semantic_report = base_dir / "semantic-layout-report.json"
    destination = base_dir / "value-profile.json"

    if not layout_report.exists():
        raise SystemExit(
            f"Relatório de layout ausente: {layout_report}. "
            "Execute rais-inspect primeiro."
        )
    if not semantic_report.exists():
        raise SystemExit(
            f"Relatório semântico ausente: {semantic_report}. "
            "Execute rais-validate-layout primeiro."
        )

    payload = profile_rais_values(
        extracted_dir,
        layout_report,
        semantic_report,
        destination,
        max_rows_per_file=max_rows_per_file,
    )
    print(
        f"rais profile: arquivos={payload['files_profiled']} "
        f"limite={payload['max_rows_per_file']} relatório={destination}"
    )
    print("rais silver transform: BLOCKED until value semantics are reviewed")


def command_rais_validate_values(year: int) -> None:
    base_dir = settings.bronze_path / "rais" / str(year)
    profile_path = base_dir / "value-profile.json"
    destination = base_dir / "value-semantics-report.json"

    if not profile_path.exists():
        raise SystemExit(
            f"Perfil de valores ausente: {profile_path}. "
            "Execute rais-profile-values primeiro."
        )

    payload = validate_value_semantics(
        profile_path,
        settings.root / "config" / "rais_value_semantics.yml",
        destination,
        year=year,
    )
    status = "READY" if payload["silver_transform_ready"] else "BLOCKED"
    print(
        f"rais value semantics: status={status} "
        f"relatório={destination}"
    )
    if not payload["silver_transform_ready"]:
        raise SystemExit(2)


def command_rais_transform(
    year: int,
    *,
    batch_size: int,
) -> None:
    base_dir = settings.bronze_path / "rais" / str(year)
    extracted_dir = base_dir / "extracted"
    layout_report = base_dir / "layout-report.json"
    semantic_report = base_dir / "semantic-layout-report.json"
    value_report = base_dir / "value-semantics-report.json"

    required_reports = (
        layout_report,
        semantic_report,
        value_report,
    )
    missing = [path for path in required_reports if not path.exists()]
    if missing:
        raise SystemExit(
            "RAIS Silver bloqueada. Relatórios ausentes: "
            + ", ".join(str(path) for path in missing)
        )

    result = transform_rais_year(
        year=year,
        extracted_dir=extracted_dir,
        layout_report_path=layout_report,
        semantic_report_path=semantic_report,
        value_semantics_report_path=value_report,
        cbo_config_path=settings.cbo_config_path,
        silver_dir=settings.silver_path,
        batch_size=batch_size,
    )
    print(
        f"rais silver: lidas={result.rows_read:,} "
        f"válidas={result.rows_valid:,} "
        f"rejeitadas={result.rows_rejected:,} "
        f"ativas={result.rows_active:,} "
        f"tech={result.rows_tech:,}"
    )
    print(f"rais silver parquet: {result.silver_path}")
    print(f"rais quality: {result.quality_path}")
    print("rais gold: BLOCKED until annual reconciliation and gate")


def command_sync_municipalities() -> None:
    municipalities = fetch_municipalities()
    if len(municipalities) < 5000:
        raise SystemExit(
            "IBGE retornou uma quantidade inesperadamente baixa de municípios."
        )
    save_municipalities(
        municipalities,
        settings.municipalities_cache_path,
    )
    print(
        f"municípios: {len(municipalities)} referências salvas em "
        f"{settings.municipalities_cache_path}"
    )


def command_sync_population(year: int) -> None:
    populations = fetch_population_estimates(year)
    if len(populations) < 5000:
        raise SystemExit(
            "SIDRA retornou uma quantidade inesperadamente baixa de municípios."
        )
    save_population_cache(
        populations,
        year=year,
        destination=settings.population_cache_path,
    )
    print(
        f"população: {len(populations)} municípios salvos em "
        f"{settings.population_cache_path} referência={year}-07-01"
    )


def command_sync_ipca(periods: list[str], base_competence: str) -> None:
    requested = sorted(set(periods + [base_competence]))
    indices = fetch_ipca_indices(requested)
    missing = [period for period in requested if period not in indices]
    if missing:
        raise SystemExit(
            "SIDRA não retornou todas as competências solicitadas: "
            + ", ".join(missing)
        )
    save_ipca_cache(
        indices,
        base_competence=base_competence,
        destination=settings.ipca_cache_path,
    )
    print(
        f"ipca: {len(indices)} competências salvas em "
        f"{settings.ipca_cache_path} base={base_competence}"
    )


def command_load_postgres(yearmonth: str) -> None:
    try:
        result = load_approved_release(
            database_url=settings.database_url,
            yearmonth=yearmonth,
            bronze_dir=settings.bronze_path,
            gold_dir=settings.gold_path,
            reference_path=settings.reference_totals_path,
            approvals_path=settings.publication_approvals_path,
        )
    except ReleaseNotApprovedError as exc:
        raise SystemExit(str(exc)) from exc

    print(
        f"postgres: competência={result.competence} "
        f"ufs={result.uf_rows} ocupações={result.occupation_rows} "
        f"municípios={result.municipality_rows} "
        f"sha256={result.source_sha256}"
    )


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

    rais_discover = sub.add_parser(
        "rais-discover",
        help="Lista arquivos anuais da RAIS no FTP oficial do MTE.",
    )
    rais_discover.add_argument("year", type=int, help="Ano-base da RAIS.")
    rais_discover.add_argument(
        "--dataset",
        choices=["vinculos", "estabelecimentos"],
        default="vinculos",
    )

    rais_download = sub.add_parser(
        "rais-download",
        help="Baixa a camada Bronze anual da RAIS com manifests SHA-256.",
    )
    rais_download.add_argument("year", type=int, help="Ano-base da RAIS.")
    rais_download.add_argument(
        "--dataset",
        choices=["vinculos", "estabelecimentos"],
        default="vinculos",
    )

    rais_extract = sub.add_parser(
        "rais-extract",
        help="Extrai os arquivos anuais RAIS e cria manifests dos arquivos resultantes.",
    )
    rais_extract.add_argument("year", type=int, help="Ano-base da RAIS.")

    rais_inspect = sub.add_parser(
        "rais-inspect",
        help="Inspeciona o layout real dos arquivos RAIS extraídos.",
    )
    rais_inspect.add_argument("year", type=int, help="Ano-base da RAIS.")

    rais_validate_layout = sub.add_parser(
        "rais-validate-layout",
        help="Valida semanticamente o layout RAIS contra o contrato versionado.",
    )
    rais_validate_layout.add_argument("year", type=int, help="Ano-base da RAIS.")

    rais_profile = sub.add_parser(
        "rais-profile-values",
        help="Perfila valores dos conceitos RAIS antes da transformação Silver.",
    )
    rais_profile.add_argument("year", type=int, help="Ano-base da RAIS.")
    rais_profile.add_argument(
        "--max-rows-per-file",
        type=int,
        default=10000,
        help="Máximo de linhas amostradas por arquivo, até 100000.",
    )

    rais_validate_values = sub.add_parser(
        "rais-validate-values",
        help="Valida a semântica dos valores RAIS antes do Silver.",
    )
    rais_validate_values.add_argument(
        "year",
        type=int,
        help="Ano-base da RAIS.",
    )

    rais_transform = sub.add_parser(
        "rais-transform",
        help="Gera Silver anual da RAIS após todas as validações semânticas.",
    )
    rais_transform.add_argument("year", type=int, help="Ano-base da RAIS.")
    rais_transform.add_argument(
        "--batch-size",
        type=int,
        default=50000,
        help="Linhas por lote de escrita Parquet, entre 1000 e 500000.",
    )

    sub.add_parser(
        "sync-municipalities",
        help="Atualiza nomes e códigos municipais pela API oficial do IBGE.",
    )

    sync_population = sub.add_parser(
        "sync-population",
        help="Atualiza estimativas municipais de população pela tabela 6579 do SIDRA.",
    )
    sync_population.add_argument(
        "year",
        type=int,
        help="Ano de referência populacional.",
    )

    sync_ipca = sub.add_parser(
        "sync-ipca",
        help="Baixa números índice do IPCA no SIDRA para salário real.",
    )
    sync_ipca.add_argument(
        "periods",
        nargs="+",
        help="Competências AAAAMM que devem ser armazenadas.",
    )
    sync_ipca.add_argument(
        "--base",
        required=True,
        help="Competência base dos valores reais.",
    )

    load_postgres = sub.add_parser(
        "load-postgres",
        help="Carrega no PostgreSQL apenas uma competência aprovada.",
    )
    load_postgres.add_argument("yearmonth", help="Competência AAAAMM")

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

    if args.command == "rais-discover":
        command_rais_discover(args.year, args.dataset)
        return

    if args.command == "rais-download":
        command_rais_download(args.year, args.dataset)
        return

    if args.command == "rais-extract":
        command_rais_extract(args.year)
        return

    if args.command == "rais-inspect":
        command_rais_inspect(args.year)
        return

    if args.command == "rais-validate-layout":
        command_rais_validate_layout(args.year)
        return

    if args.command == "rais-profile-values":
        command_rais_profile_values(
            args.year,
            max_rows_per_file=args.max_rows_per_file,
        )
        return

    if args.command == "rais-validate-values":
        command_rais_validate_values(args.year)
        return

    if args.command == "rais-transform":
        command_rais_transform(
            args.year,
            batch_size=args.batch_size,
        )
        return

    if args.command == "sync-municipalities":
        command_sync_municipalities()
        return

    if args.command == "sync-population":
        command_sync_population(args.year)
        return

    if args.command == "sync-ipca":
        command_sync_ipca(args.periods, args.base)
        return

    if args.command == "load-postgres":
        command_load_postgres(args.yearmonth)
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
