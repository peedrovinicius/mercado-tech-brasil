from pathlib import Path

from src.reference.municipalities import (
    load_municipalities,
    save_municipalities,
)


def test_municipality_cache_roundtrip(tmp_path: Path):
    destination = tmp_path / "municipalities.json"
    payload = {
        "230440": {
            "municipio_codigo_ibge": "2304400",
            "municipio_nome": "Fortaleza",
            "uf": "CE",
        }
    }
    save_municipalities(payload, destination)

    loaded = load_municipalities(destination)
    assert loaded["230440"]["municipio_nome"] == "Fortaleza"
    assert loaded["230440"]["municipio_codigo_ibge"] == "2304400"
