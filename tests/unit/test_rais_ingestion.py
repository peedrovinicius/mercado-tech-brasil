from pathlib import Path

import pytest

import src.ingestion.rais as rais_module
from src.ingestion.rais import (
    RaisRemoteFile,
    classify_filename,
    download_file,
    extract_year,
    select_remote_files,
    select_smallest_remote_file,
    validate_year,
)


def test_classify_rais_files():
    assert classify_filename("RAIS_VINC_PUB_NORTE.7z") == "vinculos"
    assert classify_filename("RAIS_VINC_PUB_CENTRO_OESTE.7Z") == "vinculos"
    assert classify_filename("RAIS_ESTAB_PUB.7z") == "estabelecimentos"
    assert classify_filename("README.txt") is None


def test_select_only_vinculos_and_sort():
    files = select_remote_files(
        2025,
        [
            "RAIS_VINC_PUB_SUL.7z",
            "RAIS_ESTAB_PUB.7z",
            "RAIS_VINC_PUB_NORTE.7z",
            "RAIS_VINC_PUB_NI.7z",
        ],
    )

    assert [item.filename for item in files] == [
        "RAIS_VINC_PUB_NI.7z",
        "RAIS_VINC_PUB_NORTE.7z",
        "RAIS_VINC_PUB_SUL.7z",
    ]
    assert all(item.dataset == "vinculos" for item in files)


def test_establishment_selection_is_explicit():
    files = select_remote_files(
        2025,
        ["RAIS_ESTAB_PUB.7z", "RAIS_VINC_PUB_NORTE.7z"],
        dataset="estabelecimentos",
    )

    assert [item.filename for item in files] == ["RAIS_ESTAB_PUB.7z"]


def test_remote_url_is_official_ftp():
    remote = RaisRemoteFile(
        year=2025,
        dataset="vinculos",
        filename="RAIS_VINC_PUB_NORTE.7z",
    )

    assert remote.remote_dir == "pdet/microdados/RAIS/2025"
    assert remote.url == (
        "ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2025/"
        "RAIS_VINC_PUB_NORTE.7z"
    )


def test_invalid_year_and_dataset_are_rejected():
    with pytest.raises(ValueError):
        validate_year(1900)

    with pytest.raises(ValueError):
        select_remote_files(2025, [], dataset="qualquer")


def test_manifest_source_path_is_not_required_for_selection(tmp_path: Path):
    assert tmp_path.exists()



def test_extract_year_preserves_source_metadata(
    monkeypatch,
    tmp_path: Path,
):
    archive_dir = tmp_path / "archives"
    extracted_dir = tmp_path / "extracted"
    archive_dir.mkdir()
    extracted_dir.mkdir()

    archive = archive_dir / "RAIS_VINC_PUB_TESTE.7z"
    archive.write_bytes(b"archive")
    (archive_dir / "download-manifest.json").write_text(
        """{
  "files": [
    {
      "path": "RAIS_VINC_PUB_TESTE.7z",
      "transport": "ftp_mte",
      "source_url": "ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2025/RAIS_VINC_PUB_TESTE.7z"
    }
  ]
}""",
        encoding="utf-8",
    )

    extracted = extracted_dir / "RAIS_VINC_PUB_TESTE.comt"
    extracted.write_text(
        "Ano;CBO;Municipio;UF;Ativo\n2025;212405;2304400;CE;1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        rais_module,
        "extract_7z",
        lambda _archive, _destination: [extracted],
    )

    result = extract_year(2025, archive_dir, extracted_dir)

    assert result == [extracted]
    manifest = extracted.with_suffix(".comt.manifest.json")
    assert manifest.exists()
    payload = __import__("json").loads(manifest.read_text(encoding="utf-8"))
    assert payload["source"] == "rais_mte"
    assert payload["competence"] == "2025"
    assert payload["transport"] == "ftp_mte"
    assert payload["source_url"].endswith("RAIS_VINC_PUB_TESTE.7z")



def test_select_smallest_remote_file_prefers_regular_region():
    remotes = select_remote_files(
        2025,
        [
            "RAIS_VINC_PUB_NI.7z",
            "RAIS_VINC_PUB_NORTE.7z",
            "RAIS_VINC_PUB_SUL.7z",
        ],
    )
    sizes = {
        "RAIS_VINC_PUB_NI.7z": 10,
        "RAIS_VINC_PUB_NORTE.7z": 100,
        "RAIS_VINC_PUB_SUL.7z": 200,
    }

    selected = select_smallest_remote_file(remotes, sizes)

    assert selected.filename == "RAIS_VINC_PUB_NORTE.7z"


def test_download_file_resumes_after_connection_reset(
    monkeypatch,
    tmp_path: Path,
):
    rests: list[int | None] = []
    attempts = {"count": 0}

    class FakeFTP:
        def __init__(self, host: str, timeout: int):
            self.host = host
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def login(self):
            return "ok"

        def cwd(self, _path: str):
            return "ok"

        def voidcmd(self, _command: str):
            return "ok"

        def size(self, _filename: str):
            return 6

        def retrbinary(
            self,
            _command: str,
            callback,
            blocksize: int = 8192,
            rest: int | None = None,
        ):
            rests.append(rest)
            attempts["count"] += 1
            if attempts["count"] == 1:
                callback(b"abc")
                raise ConnectionResetError("queda simulada")
            callback(b"def")
            return "ok"

    monkeypatch.setattr(rais_module, "FTP", FakeFTP)
    monkeypatch.setattr(rais_module.time, "sleep", lambda _seconds: None)

    remote = RaisRemoteFile(
        year=2025,
        dataset="vinculos",
        filename="RAIS_VINC_PUB_NORTE.7z",
    )
    path = download_file(
        remote,
        tmp_path,
        max_attempts=2,
    )

    assert path.read_bytes() == b"abcdef"
    assert rests == [None, 3]
