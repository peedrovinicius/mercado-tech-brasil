import gzip
import json
from pathlib import Path

from src.reference.municipalities import (
    _decode_json_body,
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


def test_decode_json_body_supports_gzip():
    payload = [{"id": 2304400, "nome": "Fortaleza"}]
    body = gzip.compress(json.dumps(payload).encode("utf-8"))

    assert _decode_json_body(body, content_encoding="gzip") == payload


def test_decode_json_body_detects_gzip_magic_without_header():
    payload = [{"id": 3550308, "nome": "São Paulo"}]
    body = gzip.compress(json.dumps(payload).encode("utf-8"))

    assert _decode_json_body(body) == payload
