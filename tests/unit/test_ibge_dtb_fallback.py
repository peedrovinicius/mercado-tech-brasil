import io
import json
import zipfile
from hashlib import sha256
from pathlib import Path
from urllib.error import URLError

import pytest
import xlrd

from src.reference import municipalities as ibge

MUNICIPALITIES = [
    ("11", "1100015", "Alta Floresta D'Oeste"),
    ("23", "2304400", "Fortaleza"),
    ("35", "3550308", "São Paulo"),
    ("41", "4106902", "Curitiba"),
    ("53", "5300108", "Brasília"),
]


class FakeSheet:
    nrows = 7 + len(MUNICIPALITIES)

    def cell_value(self, row: int, column: int) -> str:
        if row == 6:
            return {0: "UF", 7: "Código Município Completo", 8: "Nome_Município"}.get(
                column, ""
            )
        state, code, name = MUNICIPALITIES[row - 7]
        return {0: state, 7: code, 8: name}.get(column, "")


class FakeBook:
    def sheet_by_name(self, name: str) -> FakeSheet:
        assert name == "DTB_Municípios"
        return FakeSheet()


class FakeResponse(io.BytesIO):
    def geturl(self) -> str:
        return ibge.IBGE_DTB_URL


def _mock_dtb_zip(monkeypatch: pytest.MonkeyPatch) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(ibge.IBGE_DTB_MEMBER, b"fake-xls-test")
    payload = stream.getvalue()
    monkeypatch.setattr(ibge, "IBGE_DTB_SHA256", sha256(payload).hexdigest())
    monkeypatch.setattr(ibge, "IBGE_DTB_MUNICIPALITIES", len(MUNICIPALITIES))
    monkeypatch.setattr(
        ibge,
        "urlopen",
        lambda request, timeout: FakeResponse(payload),
    )
    monkeypatch.setattr(
        xlrd,
        "open_workbook",
        lambda *, file_contents: FakeBook(),
    )
    return payload


def test_dtb_fallback_validates_pinned_hash_and_5571_style_mapping(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_dtb_zip(monkeypatch)
    result = ibge.fetch_municipalities_dtb(timeout=10)

    assert len(result) == len(MUNICIPALITIES)
    assert result["230440"]["uf"] == "CE"
    assert result["355030"]["municipio_codigo_ibge"] == "3550308"
    assert result.source == "IBGE Divisão Territorial Brasileira 2025"

    destination = tmp_path / "municipios.json"
    ibge.save_municipalities(result, destination)
    provenance = json.loads(destination.read_text(encoding="utf-8"))
    assert provenance["source"] == "IBGE Divisão Territorial Brasileira 2025"
    assert provenance["url"] == ibge.IBGE_DTB_URL
    assert provenance["archive_sha256"] == ibge.IBGE_DTB_SHA256


def test_dtb_fallback_rejects_changed_official_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _mock_dtb_zip(monkeypatch)
    monkeypatch.setattr(ibge, "IBGE_DTB_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="SHA-256"):
        ibge.fetch_municipalities_dtb(timeout=10)
    assert sha256(payload).hexdigest() != "0" * 64


def test_official_api_failure_uses_pinned_dtb_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_dtb_zip(monkeypatch)

    def timeout(url: str, *, timeout: int) -> object:
        raise URLError("timeout")

    monkeypatch.setattr(ibge, "_fetch_municipalities_payload", timeout)
    result = ibge.fetch_municipalities(timeout=10)
    assert len(result) == len(MUNICIPALITIES)
    assert result.source == "IBGE Divisão Territorial Brasileira 2025"
