from pathlib import Path

import yaml

EXPECTED_V2_FAMILIES = {
    "2122": "Engenheiros em computação",
    "2123": "Administradores de tecnologia da informação",
    "2124": "Analistas de tecnologia da informação",
    "3171": "Técnicos de desenvolvimento de sistemas e aplicações",
    "3172": "Técnicos em operação e monitoração de computadores",
}


def test_cbo_scope_v2_is_explicit_and_complete():
    payload = yaml.safe_load(Path("config/cbo_tech.yml").read_text(encoding="utf-8"))

    assert payload["version"] == 2
    assert payload["families"] == EXPECTED_V2_FAMILIES
    assert "sources" in payload
    assert "rationale" in payload


def test_cbo_scope_contains_engineers_in_computing():
    payload = yaml.safe_load(Path("config/cbo_tech.yml").read_text(encoding="utf-8"))

    assert payload["families"]["2122"] == "Engenheiros em computação"
