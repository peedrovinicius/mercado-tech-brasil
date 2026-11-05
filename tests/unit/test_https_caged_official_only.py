from pathlib import Path

import pytest

from src.ingestion import https_caged


def test_official_only_fails_closed_when_mte_ftp_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def unavailable(*args: object, **kwargs: object) -> list[Path]:
        raise OSError("FTP indisponível")

    def forbidden_mirror(*args: object, **kwargs: object) -> None:
        pytest.fail("O modo official_only não deve acessar o espelho externo")

    monkeypatch.setattr(https_caged, "download_month", unavailable)
    monkeypatch.setattr(https_caged, "download_month_https", forbidden_mirror)

    with pytest.raises(RuntimeError, match="fallback não oficial desativado"):
        https_caged.download_month_resilient(
            "202609",
            tmp_path,
            file_types=("MOV",),
            official_only=True,
        )


def test_official_only_rejects_missing_mte_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        https_caged,
        "download_month",
        lambda *args, **kwargs: [],
    )

    def forbidden_mirror(*args: object, **kwargs: object) -> None:
        pytest.fail("Arquivo ausente: não deve consultar o espelho")

    monkeypatch.setattr(https_caged, "download_month_https", forbidden_mirror)

    with pytest.raises(RuntimeError, match="fallback não oficial desativado"):
        https_caged.download_month_resilient(
            "202609",
            tmp_path,
            file_types=("EXC",),
            official_only=True,
        )


def test_official_only_uses_mte_ftp_when_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "CAGEDMOV202609.7z"
    archive.write_bytes(b"mock-official-archive")

    monkeypatch.setattr(
        https_caged,
        "download_month",
        lambda *args, **kwargs: [archive],
    )

    def forbidden_mirror(*args: object, **kwargs: object) -> None:
        pytest.fail("FTP disponível: não deve consultar o espelho")

    monkeypatch.setattr(https_caged, "download_month_https", forbidden_mirror)

    result = https_caged.download_month_resilient(
        "202609",
        tmp_path,
        file_types=("MOV",),
        official_only=True,
    )

    assert len(result) == 1
    assert result[0].transport == "ftp_mte"
    assert result[0].kind == "MOV"
    assert result[0].path == archive
    assert result[0].url.startswith("ftp://ftp.mtps.gov.br/")


def test_existing_default_fallback_remains_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def unavailable(*args: object, **kwargs: object) -> list[Path]:
        raise OSError("FTP indisponível")

    expected = https_caged.DownloadArtifact(
        path=tmp_path / "CAGEDMOV202608.7z",
        kind="MOV",
        transport="https_huggingface_mirror",
        url="https://example.invalid/test-only",
    )
    monkeypatch.setattr(https_caged, "download_month", unavailable)
    monkeypatch.setattr(
        https_caged,
        "download_month_https",
        lambda *args, **kwargs: [expected],
    )

    assert https_caged.download_month_resilient(
        "202608",
        tmp_path,
        file_types=("MOV",),
    ) == [expected]
