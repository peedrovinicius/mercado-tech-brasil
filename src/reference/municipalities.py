from __future__ import annotations

import json
from pathlib import Path
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


def fetch_municipalities(*, timeout: int = 60) -> dict[str, dict[str, str]]:
    request = Request(
        IBGE_MUNICIPALITIES_URL,
        headers={"User-Agent": "mercado-tech-brasil/0.13"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result: dict[str, dict[str, str]] = {}
    for item in payload:
        ibge_code = str(item.get("id") or "")
        name = str(item.get("nome") or "")
        uf = _uf_from_item(item)
        if len(ibge_code) != 7 or not ibge_code.isdigit() or not name or not uf:
            continue

        caged_prefix = ibge_code[:6]
        result[caged_prefix] = {
            "municipio_codigo_ibge": ibge_code,
            "municipio_nome": name,
            "uf": uf,
        }
    return result


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
