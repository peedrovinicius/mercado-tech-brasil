from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".comt", ".txt", ".csv"}
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1")


@dataclass(frozen=True)
class RaisLayoutInspection:
    file: str
    suffix: str
    encoding: str
    delimiter: str
    columns: list[str]
    normalized_columns: list[str]
    column_count: int
    header_signature_sha256: str


def normalize_column_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    cleaned = []
    previous_separator = False

    for char in normalized.strip().lower():
        if char.isalnum():
            cleaned.append(char)
            previous_separator = False
        elif not previous_separator:
            cleaned.append("_")
            previous_separator = True

    return "".join(cleaned).strip("_")


def detect_encoding(path: Path) -> str:
    sample = path.read_bytes()[:262144]
    for encoding in ENCODINGS:
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Codificação RAIS não reconhecida: {path.name}")


def _first_nonempty_line(path: Path, encoding: str) -> str:
    with path.open("r", encoding=encoding, errors="strict", newline="") as source:
        for line in source:
            if line.strip():
                return line.rstrip("\r\n")
    raise ValueError(f"Arquivo RAIS vazio: {path.name}")


def detect_delimiter(header_line: str) -> str:
    candidates = (";", "|", "\t", ",")
    counts = {candidate: header_line.count(candidate) for candidate in candidates}
    delimiter = max(counts, key=counts.get)
    if counts[delimiter] <= 0:
        raise ValueError("Não foi possível detectar delimitador no cabeçalho RAIS.")
    return delimiter


def inspect_rais_file(path: Path) -> RaisLayoutInspection:
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Extensão RAIS não suportada: {path.suffix}")

    encoding = detect_encoding(path)
    header_line = _first_nonempty_line(path, encoding)
    delimiter = detect_delimiter(header_line)
    columns = next(csv.reader([header_line], delimiter=delimiter))
    columns = [column.strip().strip('"') for column in columns]
    normalized = [normalize_column_name(column) for column in columns]

    if len(columns) < 5:
        raise ValueError(
            f"Cabeçalho RAIS com poucas colunas: {path.name} ({len(columns)})"
        )
    if any(not column for column in normalized):
        raise ValueError(f"Cabeçalho RAIS possui coluna vazia: {path.name}")
    if len(set(normalized)) != len(normalized):
        raise ValueError(
            f"Cabeçalho RAIS gera nomes normalizados duplicados: {path.name}"
        )

    signature = hashlib.sha256(
        "\n".join(normalized).encode("utf-8")
    ).hexdigest()

    return RaisLayoutInspection(
        file=path.name,
        suffix=path.suffix.lower(),
        encoding=encoding,
        delimiter=delimiter,
        columns=columns,
        normalized_columns=normalized,
        column_count=len(columns),
        header_signature_sha256=signature,
    )


def inspect_rais_directory(
    directory: Path,
    *,
    year: int,
    destination: Path,
) -> dict[str, object]:
    files = sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo RAIS extraído suportado em {directory}"
        )

    inspections = [inspect_rais_file(path) for path in files]
    signatures = sorted(
        {item.header_signature_sha256 for item in inspections}
    )

    payload: dict[str, object] = {
        "source": "RAIS / Ministério do Trabalho e Emprego",
        "year": year,
        "purpose": "inspeção de layout antes da transformação Silver",
        "supported_suffixes": sorted(SUPPORTED_SUFFIXES),
        "files_inspected": len(inspections),
        "unique_layouts": len(signatures),
        "layout_signatures": signatures,
        "files": [asdict(item) for item in inspections],
        "silver_ready": False,
        "publication_ready": False,
        "note": (
            "O relatório registra o layout observado. A transformação Silver "
            "só deve ser implementada após validar semanticamente as colunas "
            "necessárias no dicionário oficial do ano."
        ),
    }

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload
