from urllib.error import URLError

import pytest

from src.reference import municipalities as ibge


def _item(code: int, name: str, state: str) -> dict:
    return {
        "id": code,
        "nome": name,
        "microrregiao": {
            "mesorregiao": {
                "UF": {"sigla": state},
            }
        },
    }


REGIONAL_ITEMS = {
    1: _item(1100015, "Alta Floresta D'Oeste", "RO"),
    2: _item(2304400, "Fortaleza", "CE"),
    3: _item(3550308, "São Paulo", "SP"),
    4: _item(4106902, "Curitiba", "PR"),
    5: _item(5300108, "Brasília", "DF"),
}


def test_national_municipalities_do_not_request_regions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ibge, "MIN_IBGE_MUNICIPALITIES", 5)

    def national_only(url: str, *, timeout: int) -> list[dict]:
        assert url == ibge.IBGE_MUNICIPALITIES_URL
        assert timeout == 10
        return list(REGIONAL_ITEMS.values())

    monkeypatch.setattr(ibge, "_fetch_municipalities_payload", national_only)
    result = ibge.fetch_municipalities(timeout=10)
    assert len(result) == 5
    assert result["230440"]["municipio_nome"] == "Fortaleza"


def test_timeout_uses_all_five_official_region_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ibge, "MIN_IBGE_MUNICIPALITIES", 5)
    requested: list[str] = []

    def fallback(url: str, *, timeout: int) -> list[dict]:
        requested.append(url)
        if url == ibge.IBGE_MUNICIPALITIES_URL:
            raise URLError("timeout")
        for region, item in REGIONAL_ITEMS.items():
            if url.endswith(f"/regioes/{region}/municipios"):
                assert timeout == 10
                return [item]
        pytest.fail(f"URL externa inesperada: {url}")

    monkeypatch.setattr(ibge, "_fetch_municipalities_payload", fallback)
    result = ibge.fetch_municipalities(timeout=10)
    assert len(result) == 5
    assert len(requested) == 6
    assert all("servicodados.ibge.gov.br" in url for url in requested)


def test_regional_response_cannot_be_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ibge, "MIN_IBGE_MUNICIPALITIES", 5)

    def partial(url: str, *, timeout: int) -> list[dict]:
        if url == ibge.IBGE_MUNICIPALITIES_URL:
            raise TimeoutError("timeout")
        for region, item in REGIONAL_ITEMS.items():
            if url.endswith(f"/regioes/{region}/municipios"):
                return [item] if region != 5 else []
        pytest.fail(f"URL externa inesperada: {url}")

    monkeypatch.setattr(ibge, "_fetch_municipalities_payload", partial)
    def no_dtb(*, timeout: int):
        raise ValueError("DTB oficial indisponível")

    monkeypatch.setattr(ibge, "fetch_municipalities_dtb", no_dtb)
    with pytest.raises(ValueError, match="DTB oficial indisponível"):
        ibge.fetch_municipalities(timeout=10)


def test_regional_response_requires_minimum_municipalities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ibge, "MIN_IBGE_MUNICIPALITIES", 6)

    def small(url: str, *, timeout: int) -> list[dict]:
        if url == ibge.IBGE_MUNICIPALITIES_URL:
            return []
        for region, item in REGIONAL_ITEMS.items():
            if url.endswith(f"/regioes/{region}/municipios"):
                return [item]
        pytest.fail(f"URL externa inesperada: {url}")

    monkeypatch.setattr(ibge, "_fetch_municipalities_payload", small)
    def no_dtb(*, timeout: int):
        raise ValueError("DTB oficial indisponível")

    monkeypatch.setattr(ibge, "fetch_municipalities_dtb", no_dtb)
    with pytest.raises(ValueError, match="DTB oficial indisponível"):
        ibge.fetch_municipalities(timeout=10)
