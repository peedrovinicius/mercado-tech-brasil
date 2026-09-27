from __future__ import annotations

import io
import json
import re
import unicodedata
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

DTB_2025_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/"
    "estrutura_territorial/divisao_territorial/2025/DTB_2025.zip"
)
RESIDUAL_MUNICIPALITY_CODE = "999999"

VALID_UF_PREFIXES = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


@dataclass(frozen=True)
class RaisMunicipalityValidation:
    year: int
    silver_rows: int
    unique_codes: int
    residual_rows: int
    residual_code_present: bool
    ibge_codes: int
    matched_codes: int
    unmatched_codes: tuple[str, ...]
    ambiguous_prefixes: tuple[str, ...]
    uf_mismatch_rows: int
    invalid_length_codes: tuple[str, ...]
    invalid_numeric_codes: tuple[str, ...]
    municipality_ready: bool
    source_url: str


def _cell_text(cell: ET.Element) -> str:
    text = " ".join(
        value.strip()
        for value in ("".join(node.itertext()) for node in cell)
        if value.strip()
    )
    if text:
        return text
    for key, value in cell.attrib.items():
        if key.endswith("}value") and str(value).strip():
            return str(value).strip()
    return ""


def _valid_ibge_code(value: str) -> bool:
    return (
        len(value) == 7
        and value.isdigit()
        and value[:2] in VALID_UF_PREFIXES
    )


def extract_ibge_municipality_codes_from_dtb(dtb_zip: bytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(dtb_zip)) as outer:
        ods_names = [
            name
            for name in outer.namelist()
            if name.lower().endswith(".ods")
            and "municip" in _normalize_text(name)
        ]
        if not ods_names:
            ods_names = [
                name
                for name in outer.namelist()
                if name.lower().endswith(".ods")
            ]
        if not ods_names:
            raise ValueError("DTB 2025 não contém planilha ODS.")

        candidates: set[str] = set()
        for ods_name in ods_names:
            with zipfile.ZipFile(io.BytesIO(outer.read(ods_name))) as ods:
                if "content.xml" not in ods.namelist():
                    continue
                root = ET.fromstring(ods.read("content.xml"))
                for cell in root.iter():
                    if not cell.tag.endswith("table-cell"):
                        continue
                    value = _cell_text(cell)
                    for token in re.findall(r"(?<!\d)\d{7}(?!\d)", value):
                        if _valid_ibge_code(token):
                            candidates.add(token)

        if not 5500 <= len(candidates) <= 5600:
            raise ValueError(
                "Quantidade inesperada de códigos municipais na DTB 2025: "
                f"{len(candidates)}"
            )
        return candidates


def fetch_dtb_2025(*, timeout: int = 60) -> bytes:
    request = urllib.request.Request(
        DTB_2025_URL,
        headers={"User-Agent": "mercado-tech-brasil/0.39"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    ).casefold()


def validate_rais_municipalities(
    *,
    silver_path: Path,
    ibge_codes: set[str],
    year: int,
) -> RaisMunicipalityValidation:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "PyArrow é necessário para validar o Silver RAIS."
        ) from exc

    if not silver_path.exists():
        raise FileNotFoundError(silver_path)

    prefix_to_full: dict[str, str] = {}
    ambiguous: set[str] = set()
    for code in sorted(ibge_codes):
        if not _valid_ibge_code(code):
            continue
        prefix = code[:6]
        previous = prefix_to_full.get(prefix)
        if previous is not None and previous != code:
            ambiguous.add(prefix)
        else:
            prefix_to_full[prefix] = code

    table = pq.read_table(
        silver_path,
        columns=["municipio_codigo", "uf"],
    )
    codes = [str(value or "") for value in table["municipio_codigo"].to_pylist()]
    ufs = [str(value or "") for value in table["uf"].to_pylist()]

    unique = set(codes)
    non_residual = {
        code for code in unique
        if code != RESIDUAL_MUNICIPALITY_CODE
    }

    invalid_length = sorted(
        code for code in non_residual
        if len(code) != 6
    )
    invalid_numeric = sorted(
        code for code in non_residual
        if not code.isdigit()
    )

    unmatched = sorted(
        code for code in non_residual
        if code not in prefix_to_full
    )

    uf_mismatch_rows = 0
    for code, uf in zip(codes, ufs, strict=True):
        if code == RESIDUAL_MUNICIPALITY_CODE:
            if uf != "NI":
                uf_mismatch_rows += 1
            continue

        full = prefix_to_full.get(code)
        if full is None:
            continue
        expected_uf = VALID_UF_PREFIXES.get(full[:2])
        if uf != expected_uf:
            uf_mismatch_rows += 1

    residual_rows = sum(
        1 for code in codes
        if code == RESIDUAL_MUNICIPALITY_CODE
    )

    ready = (
        not ambiguous
        and not unmatched
        and not invalid_length
        and not invalid_numeric
        and uf_mismatch_rows == 0
    )

    return RaisMunicipalityValidation(
        year=year,
        silver_rows=len(codes),
        unique_codes=len(unique),
        residual_rows=residual_rows,
        residual_code_present=RESIDUAL_MUNICIPALITY_CODE in unique,
        ibge_codes=len(ibge_codes),
        matched_codes=len(non_residual) - len(unmatched),
        unmatched_codes=tuple(unmatched),
        ambiguous_prefixes=tuple(sorted(ambiguous)),
        uf_mismatch_rows=uf_mismatch_rows,
        invalid_length_codes=tuple(invalid_length),
        invalid_numeric_codes=tuple(invalid_numeric),
        municipality_ready=ready,
        source_url=DTB_2025_URL,
    )


def write_rais_municipality_validation(
    result: RaisMunicipalityValidation,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
