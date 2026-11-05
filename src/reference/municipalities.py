from __future__ import annotations

import gzip
import io
import json
import zipfile
from hashlib import sha256
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.transform.schema import UF_CODE_TO_SIGLA

IBGE_MUNICIPALITIES_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
)


def _uf_from_item(item: dict) -> str | None:
    microrregiao = item.get("microrregiao") or {}
    mesorregiao = microrregiao.get("mesorregiao") or {}
    uf = mesorregiao.get("UF") or {}
    sigla = uf.get("sigla")
    if sigla:
        return str(sigla)

    immediate = item.get("regiao-imediata") or {}
    intermediate = immediate.get("regiao-intermediaria") or {}
    uf = intermediate.get("UF") or {}
    sigla = uf.get("sigla")
    return str(sigla) if sigla else None


def _decode_json_body(body: bytes, *, content_encoding: str = ""):
    encoding = content_encoding.lower().strip()
    if encoding == "gzip" or body.startswith(b"\x1f\x8b"):
        body = gzip.decompress(body)
    return json.loads(body.decode("utf-8"))


# A API oficial também permite consultar os municípios por macrorregião.
# Esse caminho reduz o tamanho de cada resposta quando a listagem nacional expira.
IBGE_REGIONS = (1, 2, 3, 4, 5)
MIN_IBGE_MUNICIPALITIES = 5000

IBGE_DTB_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/"
    "estrutura_territorial/divisao_territorial/2025/DTB_2025.zip"
)
IBGE_DTB_SHA256 = "d077a0e48c36cf18bcc96268b4a436200c014c6b8522c1a62d894acaf39dad27"
IBGE_DTB_MEMBER = "RELATORIO_DTB_BRASIL_2025_MUNICIPIOS.xls"
IBGE_DTB_MUNICIPALITIES = 5571


class MunicipalityDataset(dict[str, dict[str, str]]):
    def __init__(
        self,
        records: dict[str, dict[str, str]],
        *,
        source: str,
        url: str,
        archive_sha256: str | None = None,
    ) -> None:
        super().__init__(records)
        self.source = source
        self.url = url
        self.archive_sha256 = archive_sha256


def fetch_municipalities_dtb(*, timeout: int = 70) -> MunicipalityDataset:
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError("Instale xlrd para ler a DTB oficial do IBGE.") from exc

    request = Request(
        IBGE_DTB_URL,
        headers={"User-Agent": "mercado-tech-brasil/0.40", "Accept": "application/zip"},
    )
    with urlopen(request, timeout=timeout) as response:
        if urlsplit(response.geturl()).hostname != "geoftp.ibge.gov.br":
            raise ValueError("Redirecionamento para host não oficial do IBGE.")
        payload = response.read(8 * 1024 * 1024 + 1)
    if len(payload) > 8 * 1024 * 1024:
        raise ValueError("DTB oficial excedeu o limite de 8 MiB.")
    actual_sha256 = sha256(payload).hexdigest()
    if actual_sha256 != IBGE_DTB_SHA256:
        raise ValueError(
            "SHA-256 da DTB 2025 alterado. Revisão metodológica obrigatória."
        )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        info = archive.getinfo(IBGE_DTB_MEMBER)
        if info.file_size > 2 * 1024 * 1024:
            raise ValueError("Planilha municipal DTB excedeu o limite de 2 MiB.")
        book = xlrd.open_workbook(file_contents=archive.read(info))
    sheet = book.sheet_by_name("DTB_Municípios")
    expected_columns = (
        "UF", "Código Município Completo", "Nome_Município"
    )
    if tuple(str(sheet.cell_value(6, idx)) for idx in (0, 7, 8)) != expected_columns:
        raise ValueError("Colunas da DTB 2025 diferentes do layout validado.")

    records: dict[str, dict[str, str]] = {}
    for row in range(7, sheet.nrows):
        state = str(sheet.cell_value(row, 0)).strip()
        code = str(sheet.cell_value(row, 7)).strip()
        name = str(sheet.cell_value(row, 8)).strip()
        if (
            len(code) != 7
            or not code.isdigit()
            or not name
            or state not in UF_CODE_TO_SIGLA
            or state == "99"
            or code[:2] != state
        ):
            raise ValueError(f"Linha municipal inválida na DTB: {row + 1}")
        prefix = code[:6]
        if prefix in records:
            raise ValueError(f"Prefixo CAGED duplicado na DTB: {prefix}")
        records[prefix] = {
            "municipio_codigo_ibge": code,
            "municipio_nome": name,
            "uf": UF_CODE_TO_SIGLA[state],
        }

    if len(records) != IBGE_DTB_MUNICIPALITIES:
        raise ValueError(
            f"DTB incompleta: {len(records)} municípios; "
            f"esperados {IBGE_DTB_MUNICIPALITIES}."
        )
    return MunicipalityDataset(
        records,
        source="IBGE Divisão Territorial Brasileira 2025",
        url=IBGE_DTB_URL,
        archive_sha256=actual_sha256,
    )


def _fetch_municipalities_payload(url: str, *, timeout: int) -> object:
    request = Request(
        url,
        headers={
            "User-Agent": "mercado-tech-brasil/0.14.1",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return _decode_json_body(
            response.read(),
            content_encoding=response.headers.get("Content-Encoding", ""),
        )


def _parse_municipalities(payload: object) -> dict[str, dict[str, str]]:
    if not isinstance(payload, list):
        raise TypeError("IBGE Localidades não retornou uma lista de municípios.")

    result: dict[str, dict[str, str]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        ibge_code = str(item.get("id") or "")
        name = str(item.get("nome") or "").strip()
        uf = _uf_from_item(item)
        if len(ibge_code) != 7 or not ibge_code.isdigit() or not name or not uf:
            continue

        caged_prefix = ibge_code[:6]
        normalized = {
            "municipio_codigo_ibge": ibge_code,
            "municipio_nome": name,
            "uf": uf,
        }
        if caged_prefix in result and result[caged_prefix] != normalized:
            raise ValueError(f"Código CAGED ambíguo no IBGE: {caged_prefix}")
        result[caged_prefix] = normalized
    return result


def _fetch_municipalities_by_region(*, timeout: int) -> dict[str, dict[str, str]]:
    base = IBGE_MUNICIPALITIES_URL.rsplit("/municipios", 1)[0]

    def fetch_region(region: int) -> dict[str, dict[str, str]]:
        url = f"{base}/regioes/{region}/municipios"
        data = _parse_municipalities(
            _fetch_municipalities_payload(url, timeout=timeout)
        )
        if not data:
            raise ValueError(f"Região IBGE {region} retornou lista vazia.")
        return data

    with ThreadPoolExecutor(max_workers=len(IBGE_REGIONS)) as executor:
        regional_results = list(executor.map(fetch_region, IBGE_REGIONS))

    combined: dict[str, dict[str, str]] = {}
    for region_result in regional_results:
        for code, item in region_result.items():
            if code in combined and combined[code] != item:
                raise ValueError(f"Código municipal IBGE inconsistente: {code}")
            combined[code] = item

    if len(combined) < MIN_IBGE_MUNICIPALITIES:
        raise ValueError(
            f"Resposta regional incompleta: {len(combined)} municípios. "
            "A auditoria não pode usar referência parcial."
        )
    return combined


def fetch_municipalities(*, timeout: int = 60) -> dict[str, dict[str, str]]:
    try:
        national = _parse_municipalities(
            _fetch_municipalities_payload(
                IBGE_MUNICIPALITIES_URL, timeout=timeout
            )
        )
        if len(national) >= MIN_IBGE_MUNICIPALITIES:
            return MunicipalityDataset(
                national,
                source="IBGE API de Localidades",
                url=IBGE_MUNICIPALITIES_URL,
            )
    except (OSError, URLError, TimeoutError, ValueError, TypeError):
        # Erros no endpoint nacional não autorizam dados incompletos.
        pass

    try:
        regional = _fetch_municipalities_by_region(timeout=timeout)
    except (OSError, URLError, TimeoutError, ValueError, TypeError):
        regional = None

    if regional is not None:
        return MunicipalityDataset(
            regional,
            source="IBGE API de Localidades (5 regiões)",
            url=IBGE_MUNICIPALITIES_URL,
        )
    return fetch_municipalities_dtb(timeout=timeout)


def save_municipalities(
    municipalities: dict[str, dict[str, str]],
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "source": getattr(
                    municipalities, "source", "IBGE API de Localidades"
                ),
                "url": getattr(
                    municipalities, "url", IBGE_MUNICIPALITIES_URL
                ),
                "archive_sha256": getattr(
                    municipalities, "archive_sha256", None
                ),
                "mapping_rule": (
                    "codigo CAGED de 6 dígitos corresponde aos 6 primeiros "
                    "dígitos do código municipal IBGE de 7 dígitos"
                ),
                "municipalities": municipalities,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def load_municipalities(path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    municipalities = payload.get("municipalities")
    if not isinstance(municipalities, dict):
        raise TypeError("Cache de municípios inválido.")
    return municipalities
