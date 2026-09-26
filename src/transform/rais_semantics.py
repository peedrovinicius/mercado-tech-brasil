from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_semantic_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Contrato semântico RAIS inválido.")

    required = payload.get("required")
    optional = payload.get("optional")
    derived = payload.get("derived")
    if not isinstance(required, dict) or not required:
        raise ValueError("Contrato RAIS não possui conceitos obrigatórios.")
    if optional is not None and not isinstance(optional, dict):
        raise TypeError("Conceitos opcionais RAIS inválidos.")
    if derived is not None and not isinstance(derived, dict):
        raise TypeError("Conceitos derivados RAIS inválidos.")

    return payload


def _aliases(spec: object) -> set[str]:
    if not isinstance(spec, dict):
        return set()
    raw = spec.get("aliases")
    if not isinstance(raw, list):
        return set()
    return {str(value).strip() for value in raw if str(value).strip()}


def _match_concept(
    columns: list[str],
    spec: object,
) -> dict[str, object]:
    accepted = _aliases(spec)
    matches = [column for column in columns if column in accepted]

    if not matches:
        status = "missing"
    elif len(matches) == 1:
        status = "matched"
    else:
        status = "ambiguous"

    return {
        "status": status,
        "matches": matches,
        "aliases": sorted(accepted),
    }


def validate_layout_semantics(
    layout_report_path: Path,
    contract_path: Path,
    destination: Path,
) -> dict[str, object]:
    layout = json.loads(layout_report_path.read_text(encoding="utf-8"))
    contract = load_semantic_contract(contract_path)

    required = contract["required"]
    optional = contract.get("optional") or {}
    derived = contract.get("derived") or {}
    files = layout.get("files") or []
    if not isinstance(files, list) or not files:
        raise ValueError("Relatório de layout RAIS não possui arquivos inspecionados.")

    file_results: list[dict[str, object]] = []
    all_required_valid = True

    for item in files:
        if not isinstance(item, dict):
            continue

        columns = item.get("normalized_columns") or []
        if not isinstance(columns, list):
            columns = []
        normalized_columns = [str(column) for column in columns]

        required_matches = {
            name: _match_concept(normalized_columns, spec)
            for name, spec in required.items()
        }
        optional_matches = {
            name: _match_concept(normalized_columns, spec)
            for name, spec in optional.items()
        }

        missing = [
            name
            for name, result in required_matches.items()
            if result["status"] == "missing"
        ]
        ambiguous = [
            name
            for name, result in required_matches.items()
            if result["status"] == "ambiguous"
        ]
        valid = not missing and not ambiguous
        all_required_valid = all_required_valid and valid

        file_results.append(
            {
                "file": item.get("file"),
                "layout_signature": item.get("header_signature_sha256"),
                "valid": valid,
                "missing_required": missing,
                "ambiguous_required": ambiguous,
                "required": required_matches,
                "optional": optional_matches,
            }
        )

    payload: dict[str, object] = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": layout.get("year"),
        "contract_version": contract.get("version"),
        "dataset": contract.get("dataset"),
        "files_validated": len(file_results),
        "semantic_valid": all_required_valid and bool(file_results),
        "silver_ready": all_required_valid and bool(file_results),
        "publication_ready": False,
        "derived": derived,
        "files": file_results,
        "note": (
            "silver_ready confirma somente que os conceitos físicos obrigatórios "
            "foram mapeados sem ambiguidade. Ano e UF são derivados pelo pipeline. "
            "A publicação continua bloqueada até transformação, reconciliação e "
            "gate anual."
        ),
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
