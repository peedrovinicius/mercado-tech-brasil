from pathlib import Path

from src.ingestion.local import ingest_local_file


def test_local_txt_is_copied_and_manifested(tmp_path: Path):
    source = tmp_path / "CAGEDMOV_TEST.txt"
    source.write_text("a;b\n1;2\n", encoding="utf-8")

    result = ingest_local_file(
        source,
        yearmonth="202607",
        kind="MOV",
        bronze_root=tmp_path / "bronze",
    )

    assert result.bronze_file.exists()
    assert len(result.extracted_files) == 1
    assert len(result.manifest_files) == 1
    assert result.manifest_files[0].exists()

    payload = result.manifest_files[0].read_text(encoding="utf-8")
    assert '"competence": "202607"' in payload
    assert '"sha256":' in payload


def test_local_ingestion_rejects_unknown_extension(tmp_path: Path):
    source = tmp_path / "dados.csv"
    source.write_text("a,b\n", encoding="utf-8")

    try:
        ingest_local_file(
            source,
            yearmonth="202607",
            kind="MOV",
            bronze_root=tmp_path / "bronze",
        )
    except ValueError as exc:
        assert ".txt ou .7z" in str(exc)
    else:
        raise AssertionError("Esperava ValueError")
