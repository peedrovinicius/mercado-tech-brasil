from src.ingestion.https_caged import build_https_remote


def test_build_https_remote_uses_expected_caged_path():
    remote = build_https_remote("202607", "MOV")

    assert remote.filename == "CAGEDMOV202607.7z"
    assert remote.url == (
        "https://huggingface.co/datasets/alexsandroprado/caged/resolve/main/"
        "NOVO_CAGED/2026/202607/CAGEDMOV202607.7z"
    )


def test_build_https_remote_supports_adjustments():
    assert build_https_remote("202607", "FOR").filename == "CAGEDFOR202607.7z"
    assert build_https_remote("202607", "EXC").filename == "CAGEDEXC202607.7z"
