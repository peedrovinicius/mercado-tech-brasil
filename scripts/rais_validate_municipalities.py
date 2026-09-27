from __future__ import annotations

import argparse
from pathlib import Path

from src.validation.rais_municipalities import (
    extract_ibge_municipality_codes_from_dtb,
    fetch_dtb_2025,
    validate_rais_municipalities,
    write_rais_municipality_validation,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--silver",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
    )
    args = parser.parse_args()

    if args.year != 2025:
        raise SystemExit("Validação municipal configurada para RAIS 2025.")

    dtb_zip = fetch_dtb_2025(timeout=90)
    ibge_codes = extract_ibge_municipality_codes_from_dtb(dtb_zip)
    result = validate_rais_municipalities(
        silver_path=args.silver,
        ibge_codes=ibge_codes,
        year=args.year,
    )
    write_rais_municipality_validation(result, args.output)

    print(f"ibge_codes={result.ibge_codes}")
    print(f"silver_rows={result.silver_rows}")
    print(f"unique_codes={result.unique_codes}")
    print(f"matched_codes={result.matched_codes}")
    print(f"unmatched_codes={len(result.unmatched_codes)}")
    print(f"uf_mismatch_rows={result.uf_mismatch_rows}")
    print(f"residual_rows={result.residual_rows}")
    print(f"municipality_ready={result.municipality_ready}")

    if not result.municipality_ready:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
