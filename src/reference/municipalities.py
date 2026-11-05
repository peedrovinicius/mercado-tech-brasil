from __future__ import annotations

import gzip
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

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
            return national
    except (OSError, URLError, TimeoutError, ValueError, TypeError):
        # Erros no endpoint nacional não autorizam dados incompletos.
        pass

    return _fetch_municipalities_by_region(timeout=timeout)


def save_municipalities(
    municipalities: dict[str, dict[str, str]],
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "source": "IBGE API de Localidades",
                "url": IBGE_MUNICIPALITIES_URL,
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
