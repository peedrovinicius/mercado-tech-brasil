from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.rais_process_pending_mirror as mirror


def test_mirror_urls_try_pinned_then_fallback():
    config = {
        "mirror_dataset": "example/dataset",
        "mirror_commit": "abc123",
        "mirror_fallback_ref": "main",
        "mirror_path_prefix": "RAIS/2025",
    }

    urls = mirror._mirror_urls(
        config,
        "RAIS_VINC_PUB_NORDESTE.7z",
    )

    assert urls == [
        (
            "https://huggingface.co/datasets/example/dataset/"
            "resolve/abc123/RAIS/2025/RAIS_VINC_PUB_NORDESTE.7z"
            "?download=true"
        ),
        (
            "https://huggingface.co/datasets/example/dataset/"
            "resolve/main/RAIS/2025/RAIS_VINC_PUB_NORDESTE.7z"
            "?download=true"
        ),
    ]


def test_download_candidates_falls_back_and_cleans_partial(
    monkeypatch,
    tmp_path: Path,
):
    destination = tmp_path / "part.7z"
    calls: list[str] = []

    def fake_download(url: str, path: Path, expected_size: int) -> None:
        calls.append(url)
        if url.endswith("/first"):
            path.write_bytes(b"partial")
            raise RuntimeError("404")
        path.write_bytes(b"ok")
        assert expected_size == 2

    monkeypatch.setattr(mirror, "_download", fake_download)

    used = mirror._download_candidates(
        ["https://x/first", "https://x/second"],
        destination,
        2,
    )

    assert used == "https://x/second"
    assert destination.read_bytes() == b"ok"
    assert calls == ["https://x/first", "https://x/second"]


def test_completed_archives_detects_existing_parts(tmp_path: Path):
    part = tmp_path / "rais-vinc-pub-norte"
    part.mkdir()
    (part / "part-summary.json").write_text(
        json.dumps(
            {
                "archive": "RAIS_VINC_PUB_NORTE.7z",
                "rows_read": 1,
            }
        ),
        encoding="utf-8",
    )

    assert mirror._completed_archives(tmp_path) == {
        "RAIS_VINC_PUB_NORTE.7z"
    }


def test_download_candidates_raises_after_all_fail(
    monkeypatch,
    tmp_path: Path,
):
    def always_fail(
        url: str,
        path: Path,
        expected_size: int,
    ) -> None:
        raise RuntimeError(f"failed {url}")

    monkeypatch.setattr(mirror, "_download", always_fail)

    with pytest.raises(RuntimeError, match="Nenhuma revisão"):
        mirror._download_candidates(
            ["https://x/a", "https://x/b"],
            tmp_path / "part.7z",
            10,
        )
