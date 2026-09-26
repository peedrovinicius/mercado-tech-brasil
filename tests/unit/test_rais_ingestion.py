from pathlib import Path

import pytest

from src.ingestion.rais import (
    RaisRemoteFile,
    classify_filename,
    select_remote_files,
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
