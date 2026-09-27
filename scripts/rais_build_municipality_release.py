from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.core.settings import settings
from src.gold.rais_municipalities import build_rais_municipality_gold
from src.reference.municipalities import fetch_municipalities
from src.validation.rais_municipalities import (
    extract_ibge_municipality_codes_from_dtb,
    fetch_dtb_2025,
    validate_rais_municipalities,
    write_rais_municipality_validation,
)
from src.validation.rais_publication_gate import (
    evaluate_rais_publication_gate,
    write_rais_publication_gate,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--silver", type=Path, required=True)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("rais-municipality-release-summary.json"),
    )
    args = parser.parse_args()

    if args.year != 2025:
        raise SystemExit("Executor municipal configurado para RAIS 2025.")

    dtb = fetch_dtb_2025(timeout=90)
    codes = extract_ibge_municipality_codes_from_dtb(dtb)

    validation_path = (
        settings.silver_path
        / f"rais_municipality_validation_{args.year}.json"
    )
    validation = validate_rais_municipalities(
        silver_path=args.silver,
        ibge_codes=codes,
        year=args.year,
    )
    write_rais_municipality_validation(
        validation,
        validation_path,
    )
    if not validation.municipality_ready:
        raise SystemExit("Dimensão municipal RAIS não foi aprovada.")

    municipality_gold = build_rais_municipality_gold(
        year=args.year,
        silver_path=args.silver,
        validation_path=validation_path,
        gold_dir=settings.gold_path,
        municipalities=fetch_municipalities(),
    )

    gate = evaluate_rais_publication_gate(
        year=args.year,
        bronze_dir=settings.bronze_path,
        silver_dir=settings.silver_path,
        gold_dir=settings.gold_path,
        approvals_path=settings.rais_publication_approvals_path,
    )
    gate_path = (
        settings.gold_path
        / f"rais-publication-gate-{args.year}.json"
    )
    write_rais_publication_gate(gate, gate_path)

    municipality_payload = json.loads(
        municipality_gold.read_text(encoding="utf-8")
    )
    summary = {
        "year": args.year,
        "municipality_validation": {
            "ibge_codes": validation.ibge_codes,
            "silver_rows": validation.silver_rows,
            "unique_codes": validation.unique_codes,
            "matched_codes": validation.matched_codes,
            "unmatched_codes": list(validation.unmatched_codes),
            "uf_mismatch_rows": validation.uf_mismatch_rows,
            "residual_rows": validation.residual_rows,
            "municipality_ready": validation.municipality_ready,
        },
        "municipality_gold": {
            "municipality_count": municipality_payload[
                "municipality_count"
            ],
            "active_stock_tech": municipality_payload[
                "active_stock_tech"
            ],
            "top_10": municipality_payload["items"][:10],
        },
        "gate": {
            "automatic_checks_passed": gate.automatic_checks_passed,
            "manual_approval_valid": gate.manual_approval_valid,
            "publishable": gate.publishable,
            "release_sha256": gate.release_sha256,
        },
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
