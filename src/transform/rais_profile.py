from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON RAIS inválido: {path}")
    return payload


def _single_file(root: Path, filename: str) -> Path:
    matches = [
        path
        for path in root.rglob(filename)
        if path.is_file()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Esperado exatamente um arquivo {filename} em {root}; "
            f"encontrados: {len(matches)}"
        )
    return matches[0]


def _concept_column(
    semantic_item: dict[str, Any],
    layout_item: dict[str, Any],
    concept: str,
) -> tuple[str, str]:
    required = semantic_item.get("required") or {}
    result = required.get(concept) or {}
    matches = result.get("matches") or []
    if result.get("status") != "matched" or len(matches) != 1:
        raise ValueError(
            f"Conceito {concept} não está resolvido sem ambiguidade "
            f"em {semantic_item.get('file')}"
        )

    normalized = str(matches[0])
    original_columns = layout_item.get("columns") or []
    normalized_columns = layout_item.get("normalized_columns") or []
    mapping = {
        str(normalized_name): str(original_name)
        for original_name, normalized_name in zip(
            original_columns,
            normalized_columns,
            strict=True,
        )
    }
    if normalized not in mapping:
        raise ValueError(
            f"Coluna normalizada {normalized} não encontrada no layout "
            f"de {semantic_item.get('file')}"
        )
    return normalized, mapping[normalized]


def _value_profile(counter: Counter[str], blanks: int) -> dict[str, object]:
    non_blank = sum(counter.values())
    length_counts = Counter(str(len(value)) for value in counter.elements())
    digits_only = sum(
        count
        for value, count in counter.items()
        if value.isdigit()
    )

    observed_values = (
        sorted(counter)
        if len(counter) <= 50
        else None
    )

    return {
        "non_blank": non_blank,
        "blank": blanks,
        "distinct_in_sample": len(counter),
        "digits_only": digits_only,
        "lengths": dict(sorted(length_counts.items())),
        "observed_values": observed_values,
        "top_values": [
            {"value": value, "count": count}
            for value, count in counter.most_common(25)
        ],
    }


def profile_rais_values(
    extracted_dir: Path,
    layout_report_path: Path,
    semantic_report_path: Path,
    destination: Path,
    *,
    max_rows_per_file: int = 10000,
) -> dict[str, object]:
    if max_rows_per_file < 1 or max_rows_per_file > 100000:
        raise ValueError("max_rows_per_file deve estar entre 1 e 100000.")

    layout = _load_json(layout_report_path)
    semantics = _load_json(semantic_report_path)

    if semantics.get("silver_ready") is not True:
        raise ValueError(
            "O perfil de valores exige validação semântica com silver_ready=true."
        )

    layout_files = {
        str(item.get("file")): item
        for item in layout.get("files", [])
        if isinstance(item, dict)
    }
    semantic_files = [
        item
        for item in semantics.get("files", [])
        if isinstance(item, dict)
    ]
    if not semantic_files:
        raise ValueError("Relatório semântico não possui arquivos validados.")

    concepts = ("year", "cbo_occupation", "municipality", "uf", "active_3112")
    aggregate_counters = {
        concept: Counter()
        for concept in concepts
    }
    aggregate_blanks = {
        concept: 0
        for concept in concepts
    }
    file_profiles: list[dict[str, object]] = []

    for semantic_item in semantic_files:
        filename = str(semantic_item.get("file") or "")
        if not filename:
            raise ValueError("Relatório semântico contém arquivo sem nome.")
        if semantic_item.get("valid") is not True:
            raise ValueError(
                f"Layout semântico inválido ainda presente: {filename}"
            )

        layout_item = layout_files.get(filename)
        if not isinstance(layout_item, dict):
            raise ValueError(
                f"Arquivo {filename} ausente no relatório estrutural."
            )

        source = _single_file(extracted_dir, filename)
        encoding = str(layout_item.get("encoding") or "")
        delimiter = str(layout_item.get("delimiter") or "")
        if not encoding or not delimiter:
            raise ValueError(
                f"Encoding ou delimitador ausente para {filename}."
            )

        resolved = {
            concept: _concept_column(semantic_item, layout_item, concept)
            for concept in concepts
        }
        counters = {
            concept: Counter()
            for concept in concepts
        }
        blanks = {
            concept: 0
            for concept in concepts
        }

        rows_profiled = 0
        with source.open(
            "r",
            encoding=encoding,
            errors="strict",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            if reader.fieldnames is None:
                raise ValueError(f"Cabeçalho ausente em {filename}.")

            for row in reader:
                if rows_profiled >= max_rows_per_file:
                    break
                rows_profiled += 1

                for concept, (_normalized, original) in resolved.items():
                    value = str(row.get(original) or "").strip()
                    if not value:
                        blanks[concept] += 1
                        aggregate_blanks[concept] += 1
                        continue
                    counters[concept][value] += 1
                    aggregate_counters[concept][value] += 1

        file_profiles.append(
            {
                "file": filename,
                "rows_profiled": rows_profiled,
                "max_rows_per_file": max_rows_per_file,
                "concepts": {
                    concept: {
                        "column_normalized": resolved[concept][0],
                        "column_original": resolved[concept][1],
                        **_value_profile(
                            counters[concept],
                            blanks[concept],
                        ),
                    }
                    for concept in concepts
                },
            }
        )

    payload: dict[str, object] = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": semantics.get("year"),
        "contract_version": semantics.get("contract_version"),
        "purpose": "perfil de valores antes da transformação Silver",
        "files_profiled": len(file_profiles),
        "max_rows_per_file": max_rows_per_file,
        "concepts_profiled": list(concepts),
        "files": file_profiles,
        "aggregate": {
            concept: _value_profile(
                aggregate_counters[concept],
                aggregate_blanks[concept],
            )
            for concept in concepts
        },
        "profile_complete": True,
        "silver_transform_ready": False,
        "publication_ready": False,
        "note": (
            "O perfil descreve valores observados em amostra controlada. "
            "Ele não define automaticamente quais códigos representam vínculo ativo "
            "nem autoriza transformação ou publicação."
        ),
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
